import Pokemon from "./Pokemon.js";
import "./PokemonList.css";

//generates the pokemon team as a lineup
export default function PokemonList() {
    return (
        <div className="PokemonList">
            <Pokemon />
            <Pokemon />
            <Pokemon />
            <Pokemon />
            <Pokemon />
            <Pokemon />
        </div>
    );
}