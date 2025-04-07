import os
from dotenv import load_dotenv #.env file
import requests
from fastapi import FastAPI, HTTPException #python web frameowrk
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel #data validation
from typing import List
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import google.generativeai as genai
#and uvicorn is used to start the backend server

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
    return {"message": "Welcome to the Spotify AI Pokémon App"}

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
        prompt_text = f"List exactly 6 Pokémon (just their names, comma-separated) whose vibe matches this playlist: {', '.join(track_names)}"
        model = genai.GenerativeModel("gemini-1.5-flash") #had to change from the gemini pro model bc it wasnt supported anymore
        response = model.generate_content(prompt_text)
        
        # SPECIFICALLY TAKE pokémon names from response
        pokemon_names = response.text.strip().split(",")[:6]  # Ensure we get exactly 6 Pokémon

        # Generate explanation for the Pokémon team -- had to create one long prompt or else Gemini starts tweaking with mulitple ones at the same time
        explanation_prompt = f"The following playlist has these songs: {', '.join(track_names)}. A Pokémon team was chosen for this playlist: {', '.join(pokemon_names)}. Explain why each Pokémon fits the mood and energy of this playlist BRIEFLY. Be creative but concise."
        explanation_response = model.generate_content(explanation_prompt)
        explanation_text = explanation_response.text.strip()
        
        # Fetch pokémon details from PokeAPI
        pokemon_team = []
        for name in pokemon_names:
            name = name.strip().lower()
            poke_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{name}") #from the name, we look up the pokémon in the API
            if poke_response.status_code == 200:
                data = poke_response.json()
                pokemon_id = data['id']  # Get the ID of the Pokémon
                sprite_url = f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon_id}.png"
                pokemon_team.append({
                    "name": name.capitalize(),
                    "sprite": sprite_url,
                    "id": pokemon_id  
                })
            else:
                pokemon_team.append({"name": name.capitalize(), "sprite": None})
        
        return {"pokemon_team": pokemon_team, "explanation": explanation_text} # we get both of the returns
    except Exception as e:
        return {"error": str(e)}
    
    
    
