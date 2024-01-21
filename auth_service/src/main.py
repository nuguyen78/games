from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
import os
from dotenv import load_dotenv
import uvicorn


load_dotenv()

app = FastAPI()

#Google init
google_client_id = os.getenv("GOOGLE_CLIENT_ID")
google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
secret_key = os.getenv("SECRET_KEY")

oauth = OAuth()

oauth.register(
    name="google",
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_id=google_client_id,
    client_secret=google_client_secret,
    client_kwargs={'scope': 'openid email profile'},
)

app.add_middleware(SessionMiddleware, secret_key=secret_key)


#Endpointy
@app.get('/')
async def root():
    return HTMLResponse('''
<body>
    <a href="/auth/login">Log In with Google</a>
</body>''')

@app.get('/auth/me')
async def root():
    return HTMLResponse('''
<body>
    <a href="/auth/login">hello world</a>
</body>''')

@app.get('/auth/login')
async def login(request: Request):
    #return RedirectResponse(url='/auth/me')
    redirect_uri = "http://localhost:8000/callback"  
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/callback')
async def callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if user_info:
            request.session['user'] = user_info
            return RedirectResponse(url='/auth/me')
        else:
            raise HTTPException(status_code=401, detail="Failed to login")
    except Exception as e:
        return {"error": str(e)}
 


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)

    