import os
from dotenv import load_dotenv #.env file
import requests
from fastapi import FastAPI, HTTPException #python web framework
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel #data validation
from typing import List
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import google.generativeai as genai
#and uvicorn is used to start the backend server
import random #this is for the random shiny pokemon update 4/9/25

# .env 
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# geminiAPi
genai.configure(api_key=GOOGLE_API_KEY)


sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
))


app = FastAPI()

#connects the frontend 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], #changed it from the 5173 to 3000, cuz 3000 should be React LH not the React + Vite one
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# playlist
class Track(BaseModel):
    name: str
    artist: str
    uri: str

@app.get("/")
def read_root():
    return {"message": "Welcome to Pokéify!"}

#login to spotify
@app.get("/login")
async def login():
    return {
        "url": f"https://accounts.spotify.com/authorize"
               f"?client_id={SPOTIFY_CLIENT_ID}"
               f"&redirect_uri=http://localhost:3000/callback"
               f"&response_type=code"
               f"&scope=playlist-read-private"
    }



@app.get("/callback")
async def callback(code: str):
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:3000/callback",
        "client_id": SPOTIFY_CLIENT_ID,
        "client_secret": SPOTIFY_CLIENT_SECRET,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_response = requests.post(token_url, data=payload, headers=headers)
    if token_response.status_code != 200: #200 is the code that signals that it works
        raise HTTPException(status_code=500, detail="Failed to authenticate with Spotify")
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=500, detail="Missing access token")
    return {"access_token": access_token}

@app.post("/generate-pokemon-team")
async def generate_pokemon_team(tracks: List[Track]):
    if not tracks:
        raise HTTPException(status_code=400, detail="No tracks provided for analysis") #apparently error is 400 for spotify PLAYLIST okayyy
    try:
        track_names = [f"{track.name} by {track.artist}" for track in tracks]
        prompt_text = f"List exactly 6 Pokémon (just their names, comma-separated) whose vibe matches this playlist: {', '.join(track_names)}. Do not choose any shinies, or any Alolan pokémon."
        model = genai.GenerativeModel("gemini-1.5-flash") #had to change from the gemini pro model bc it wasnt supported anymore
        response = model.generate_content(prompt_text)
        
    

        # SPECIFICALLY TAKE pokémon names from response
        pokemon_names = response.text.strip().split(",")[:6]  # Ensure we get exactly 6 Pokémon

        enforcePokemonprompt = f"For every pokémon chosen in: {', '.join(pokemon_names)} -- list ONLY their corresponding ID number, NO extra 0s only their specific number."
        #make separate prompt that ties back to the pokemon names that asks Gemini to keep track of the pokemon number in accordance to the pokemon
        # to fix the issue of some pokemon not popping up -- i made it the enforcePokemonprompt
        # gonna experiment by making a response_2 but it wont print anything on the front end

        response_2 = model.generate_content(enforcePokemonprompt)
        #this will be used to be stripped in the indetification_nums


        #now im also gonna take SPECIFICALLY the ID numbers
        identification_nums = response_2.text.strip().split(",")[:6]

        # Generate explanation for the Pokémon team -- had to create one long prompt or else Gemini starts tweaking with mulitple ones at the same time
        explanation_prompt = f"The following playlist has these songs: {', '.join(track_names)}. A Pokémon team was chosen for this playlist: {', '.join(pokemon_names)}. Explain why each Pokémon fits the mood and energy of this playlist BRIEFLY. Be creative but concise."
        explanation_response = model.generate_content(explanation_prompt)
        explanation_text = explanation_response.text.strip()
        
        


        pokemon_team = []
        index = 0  # keep track of the index for fallback id or else we get multiple pokemon
        
        for name in pokemon_names:
            name = name.strip().lower()
            poke_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}")  # from the name, we look up the Pokémon in the API

            if poke_response.status_code == 200:
                data = poke_response.json()
                pokemon_id = data['id']
                shiny = random.randint(1, 4096) == 1
                sprite_url = (
                    f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pokemon_id}.png"
                    if shiny else
                    f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"
                    )
                pokemon_team.append({
                    "name": name.capitalize(),
                    "sprite": sprite_url,
                    "id": pokemon_id
                    })
            else:
                if index < len(identification_nums):
                    fallback_id = identification_nums[index].strip()
                    pokemon_id = fallback_id
                    shiny = random.randint(1, 4096) == 1
                    sprite_url = (
                        f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/shiny/{pokemon_id}.png"
                        if shiny else
                        f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"
                        )
                    pokemon_team.append({
                        "name": name.capitalize(),
                        "sprite": sprite_url,
                        "id": pokemon_id
                        })
            index += 1  # increment after every pokemon name listed or else we get ode pokemon

        return {"pokemon_team": pokemon_team, "explanation": explanation_text} # we get both of the returns
    except Exception as e:
        return {"error": str(e)}
    
    
