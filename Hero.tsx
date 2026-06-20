import { useEffect, useState } from "react";

interface HeroProps {
    name: string;
}

const Hero = ({ name }: HeroProps) => {

    const [count, setCount] = useState(0);

    const handleIncrement = () => {
        setCount(count + 1);
    };

    const handleReset = () => {
        setCount(0);
    };

    function greetUser() {
        console.log(`Hello ${name}`);
    }

    useEffect(() => {
        greetUser();
    }, []);

    return (
        <div>
            <h1>Hello {name}</h1>

            <p>Count: {count}</p>

            <button onClick={handleIncrement}>
                Increment
            </button>

            <button onClick={handleReset}>
                Reset
            </button>
        </div>
    );
};

export default Hero;