const BASE_URL = import.meta.env.VITE_API_URL || (
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://localhost:8000"
        : ""
);


export async function signup(username, email, password) {
    const response = await fetch(`${BASE_URL}/auth/signup`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username, email, password })
    });
    
    const data = await response.json();
    if (!response.ok) {
        let errorMsg = "Signup failed";
        if (typeof data.detail === "string") {
            errorMsg = data.detail;
        } else if (Array.isArray(data.detail)) {
            errorMsg = data.detail.map(err => err.msg.replace(/^Value error, /, '')).join(". ");
        }
        throw new Error(errorMsg);
    }
    return data;
}


export async function login(usernameOrEmail, password) {
    const response = await fetch(`${BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ username_or_email: usernameOrEmail, password })
    });
    
    const data = await response.json();
    if (!response.ok) {
        let errorMsg = "Login failed";
        if (typeof data.detail === "string") {
            errorMsg = data.detail;
        } else if (Array.isArray(data.detail)) {
            errorMsg = data.detail.map(err => err.msg.replace(/^Value error, /, '')).join(". ");
        }
        throw new Error(errorMsg);
    }
    return data; // Returns { access_token, token_type, username }
}


export async function streamAnswer(
    repo_url,
    question,
    onChunk,
    geminiApiKey = "",
    openrouterApiKey = ""
) {
    const token = localStorage.getItem("token");
    const headers = {
        "Content-Type": "application/json"
    };
    
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    if (geminiApiKey) {
        headers["x-gemini-api-key"] = geminiApiKey;
    }
    
    if (openrouterApiKey) {
        headers["x-openrouter-api-key"] = openrouterApiKey;
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


export async function getRepoFiles(repoUrl) {
    const token = localStorage.getItem("token");
    const headers = {};
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const response = await fetch(`${BASE_URL}/files?repo_url=${encodeURIComponent(repoUrl)}`, {
        method: "GET",
        headers
    });
    if (response.status === 401) {
        throw new Error("unauthorized");
    }
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to load files");
    }
    return data.files;
}


export async function getFileContent(repoUrl, filePath) {
    const token = localStorage.getItem("token");
    const headers = {};
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    const response = await fetch(
        `${BASE_URL}/file-content?repo_url=${encodeURIComponent(repoUrl)}&file_path=${encodeURIComponent(filePath)}`,
        {
            method: "GET",
            headers
        }
    );
    if (response.status === 401) {
        throw new Error("unauthorized");
    }
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to load file content");
    }
    return data.content;
}