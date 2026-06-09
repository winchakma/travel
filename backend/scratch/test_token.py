import sys
import time
from agora_token_builder import RtcTokenBuilder

print("RtcTokenBuilder imported successfully!")
print("Attributes:", dir(RtcTokenBuilder))

# Test token generation
try:
    token = RtcTokenBuilder.buildTokenWithUid(
        "5e5cbeafd9274ac18f86be6910c690d6",
        "0a4d3f814a2b4dafa56701e558c94354",
        "test-channel",
        12345,
        1, # Role
        int(time.time()) + 3600
    )
    print("Generated token successfully:", token)
except Exception as e:
    print("Token generation failed:", e)
