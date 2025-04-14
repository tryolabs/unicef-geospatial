export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  username: string;
}

export interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  token: string | null;
}
