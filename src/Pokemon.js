import "./Pokemon.css";

//generates the pokemon image
export default function Pokemon() {
    const randomNum = Math.floor((Math.random() * 1025) + 1);
    const url = `https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/${randomNum}.png`;
    return (
        <div className="RandomPoke">
            <img src={url} alt="" />
            <img src="./pokeball.png" alt="" id="pokeball" />
        </div>
    );
}