import { AuthToken, LoginCredentials } from "../types/Auth";

const API_URL = import.meta.env.VITE_BACKEND_URL;

class AuthService {
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    const formData = new URLSearchParams();
    formData.append("username", credentials.username);
    formData.append("password", credentials.password);

    const response = await fetch(`${API_URL}/token`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Login failed");
    }

    const data: AuthToken = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async getCurrentUser(): Promise<string | null> {
    const token = this.getToken();
    if (!token) {
      return null;
    }

    try {
      const response = await fetch(`${API_URL}/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch user data");
      }

      const data: { username: string } = await response.json();
      return data.username;
    } catch (error) {
      console.error("Error fetching current user:", error);
      return null;
    }
  }

  setToken(token: string): void {
    localStorage.setItem("auth_token", token);
  }

  getToken(): string | null {
    return localStorage.getItem("auth_token");
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  getAuthHeaders(): HeadersInit {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

export default new AuthService();
