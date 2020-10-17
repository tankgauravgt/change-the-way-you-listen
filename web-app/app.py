from flask import Flask

app = Flask(__name__)
#app.config['SECRET_KEY'] = 'secret_key'
# from routes import *

# import requests
# response = requests.get("http://api.open-notify.org/this-api-doesnt-exist")

from flask import Flask

from flask import render_template, request, redirect, session
from flask_session import Session
import time
import uuid
import pandas as pd

import threading

from analysis import *

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)


caches_folder = './.spotify_caches/'
if not os.path.exists(caches_folder):
    os.makedirs(caches_folder)

sp = None
all_tracks = pd.DataFrame()
t = None

def session_cache_path():
    return caches_folder + session.get('uuid')

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/callback')
def callback():
    my_analysis()

# @app.route('/my-analysis', methods=['POST', 'GET'])
@app.route('/my-analysis')
def my_analysis():
    # global sp
    # global t
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    scope = 'user-read-recently-played user-top-read user-modify-playback-state'
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=scope,
                                                cache_path=session_cache_path(),
                                                show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # TO-DO: Add a form to select the analysis of:
    #        * Past 4 weeks
    #        * Past 6 months
    #        * Past 3 years

    # Get the top genres of user based on top artists
    sp, user_name, top_genres_data = user_top_genres(auth_manager, term='medium_term')
    top_genres_data = top_genres_data.decode()
    return render_template('analysis.html', user=user_name, top_genres=top_genres_data)


# @app.route('/my-playlist', methods=['POST', 'GET'])
@app.route('/my-playlist')
def my_playlist():
    # playlist = return_playlist(sp, danceability='low', instrumentalness='high')
    # track_names, track_uris = get_playlist_tracks(sp, playlist)
    # return render_template('playlist.html', track_uris=track_uris, track_names=track_names)
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    scope = 'user-read-recently-played user-top-read user-modify-playback-state'
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=scope,
                                                cache_path=session_cache_path(),
                                                show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'


    sp, all_tracks, user_name = return_all_tracks(auth_manager)
    playlist = return_playlist(sp=sp, df=all_tracks)
    track_names, _ = get_playlist_tracks(sp, playlist)
    return render_template('playlist.html', user=user_name, track_names=track_names, features={})

@app.route('/customized-playlist', methods=['POST'])
def customized_playlist():

    features = {}
    features['danceability']     = request.form['danceability']
    features['energy']           = request.form['energy']
    features['speechiness']      = request.form['speechiness']
    features['acousticness']     = request.form['acousticness']
    features['instrumentalness'] = request.form['instrumentalness']
    features['liveness']         = request.form['liveness']
    features['valence']          = request.form['valence']
    features['tempo']            = request.form['tempo']
    
    if not session.get('uuid'):
        # Step 1. Visitor is unknown, give random ID
        session['uuid'] = str(uuid.uuid4())

    scope = 'user-read-recently-played user-top-read user-modify-playback-state'
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope=scope,
                                                cache_path=session_cache_path(),
                                                show_dialog=True)

    if request.args.get("code"):
        # Step 3. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.get_cached_token():
        # Step 2. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'


    sp, all_tracks, user_name = return_all_tracks(auth_manager)
    playlist = return_playlist(sp=sp, df=all_tracks, features=features)
    print("Printing...")
    print(playlist)
    track_names, _ = get_playlist_tracks(sp, playlist)
    return render_template('playlist.html', user=user_name, track_names=track_names, features=features)

if __name__ == '__main__':
    app.run(debug=True)
