import httpx
from typing import Optional, Dict, Any
from jose import jwt as jose_jwt # Hindari konflik nama dengan modul jwt lain
from app.core.config import settings

GOOGLE_TOKEN_INFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo" # Bisa juga v1
GOOGLE_TOKEN_EXCHANGE_URL = "https://oauth2.googleapis.com/token"

class GoogleOAuthService:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def exchange_auth_code(self, auth_code: str) -> Optional[Dict[str, Any]]:
        """Tukar serverAuthCode dengan access token, refresh token, dan id_token dari Google."""
        payload = {
            "code": auth_code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI, # Harus cocok dengan yang dikonfigurasi di GCP
            "grant_type": "authorization_code",
            "client_kwargs": {"scope": "profile email"},
        }
        try:
            response = await self.client.post(GOOGLE_TOKEN_EXCHANGE_URL, data=payload)
            response.raise_for_status() # Error jika status bukan 2xx
            token_data = response.json()
            # Mengandung: access_token, expires_in, refresh_token (jika offline access), scope, token_type, id_token
            return token_data
        except httpx.HTTPStatusError as e:
            print(f"HTTP error exchanging Google auth code: {e.response.text}")
            return None
        except Exception as e:
            print(f"Error exchanging Google auth code: {e}")
            return None

    async def get_user_info_from_google_tokens(
        self,
        google_access_token: Optional[str] = None,
        id_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Dapatkan info pengguna dari Google.
        Versi ini memprioritaskan penggunaan access_token untuk ke 'userinfo' endpoint.
        """
        if not google_access_token:
            print("DEBUG SERVICE: Tidak ada access_token Google untuk mengambil info user.")
            return None

        try:
            # LANGSUNG GUNAKAN USERINFO ENDPOINT, SUMBER DATA PROFIL TERBAIK
            headers = {"Authorization": f"Bearer {google_access_token}"}
            response = await self.client.get(GOOGLE_USER_INFO_URL, headers=headers)
            response.raise_for_status()
            user_info = response.json()
            # user_info dari endpoint ini biasanya mengandung: 
            # sub, name, given_name, family_name, picture, email, email_verified, locale
            
            # --- DEBUGGING: Cetak data dari userinfo endpoint ---
            # print("\n--- DEBUG: DATA DARI GOOGLE USERINFO ENDPOINT ---")
            # print(user_info)
            # print("-------------------------------------------------\n")
            # --- AKHIR DEBUGGING ---

            # Susun nama lengkap dari data yang ada
            name = user_info.get("name")
            if not name:
                given_name = user_info.get("given_name", "")
                family_name = user_info.get("family_name", "")
                name = f"{given_name} {family_name}".strip()

            return {
                "email": user_info.get("email"),
                "sub": user_info.get("sub"), # Google User ID
                "name": name or None,
                "picture": user_info.get("picture"),
                "email_verified": user_info.get("email_verified"),
            }

        except httpx.HTTPStatusError as e:
            print(f"DEBUG SERVICE: HTTP error saat mengambil user info: {e.response.text}")
            return None
        except Exception as e:
            print(f"DEBUG SERVICE: Error tidak terduga saat mengambil user info: {e}")
            return None

    async def verify_google_access_token_minimal(self, token: str) -> Optional[Dict[str, Any]]:
        """Verifikasi access token Google via tokeninfo endpoint (kurang detail dibanding userinfo)."""
        try:
            response = await self.client.get(GOOGLE_TOKEN_INFO_URL, params={"access_token": token})
            response.raise_for_status()
            token_info = response.json() # Mengandung aud, sub, email, email_verified, exp, dll.
            
            # Validasi audience jika perlu (cocokkan dengan Client ID yang digunakan Flutter)
            # expected_audiences = [settings.GOOGLE_ANDROID_CLIENT_ID, settings.GOOGLE_IOS_CLIENT_ID, settings.GOOGLE_CLIENT_ID]
            # if token_info.get("aud") not in filter(None, expected_audiences):
            #     print(f"Token audience mismatch: {token_info.get('aud')}")
            #     return None
            return token_info # sub, email, name, picture
        except httpx.HTTPStatusError as e:
            print(f"HTTP error verifying Google access token (tokeninfo): {e.response.text}")
            return None
        except Exception as e:
            print(f"Error verifying Google access token (tokeninfo): {e}")
            return None

# Dependensi untuk service
async def get_google_oauth_service() -> GoogleOAuthService:
    async with httpx.AsyncClient() as client:
        yield GoogleOAuthService(client)