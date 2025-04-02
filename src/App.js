import PokemonList from "./PokemonList.js";
import SpotifyLogin from "./SpotifyLogin.js";
import './App.css';


function App() {
  return (
    <div className="App">
      <h1>Pokeify your Spotify Profile</h1>
      <SpotifyLogin />
      <PokemonList />
    </div>
  );
}

export default App;
