const BASE_URL = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "";


export async function signup(username, password) {
    const response = await fetch(`${BASE_URL}/auth/signup`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Signup failed");
    }
    return data;
}


export async function login(username, password) {
    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, password })
    });
    
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Login failed");
    }
    return data; // Returns { access_token, token_type, username }
}


export async function streamAnswer(
    repo_url,
    question,
    onChunk
) {
    const token = localStorage.getItem("token");
    const headers = {
        "Content-Type": "application/json"
    };
    
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(
        `${BASE_URL}/stream`,
        {
            method: "POST",
            headers,
            body: JSON.stringify({
                repo_url,
                question
            })
        }
    );

    if (response.status === 401) {
        throw new Error("unauthorized");
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || "Failed to retrieve streaming response");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        onChunk(chunk);
    }
}