import httpx
import asyncio

async def test_live_upload():
    login_data = {"email": "winchakma123@gmail.com", "password": "win123win"}
    api_url = "https://east-blue-gym-api.onrender.com"
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        res = await client.post(f"{api_url}/api/auth/login", json=login_data)
        if res.status_code != 200:
            print("Login failed:", res.status_code, res.text)
            return
        token = res.json().get("token")
        print("Logged in successfully. Token:", token[:20], "...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Upload text proof
        data = {"text_proof": "Testing text upload from python script"}
        res = await client.post(f"{api_url}/api/workouts/verify?token={token}", data=data, headers=headers)
        print("Upload result:", res.status_code, res.text)

        # 3. Fetch Vault
        res = await client.get(f"{api_url}/api/workouts/", headers=headers)
        print("Vault items count:", len(res.json()) if res.status_code == 200 else res.status_code)
        if res.status_code == 200:
            items = res.json()
            for idx, item in enumerate(items[:3]):
                print(f"Item {idx}: {item}")

if __name__ == "__main__":
    asyncio.run(test_live_upload())
