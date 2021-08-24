import  time, re, spotipy, pytube, configparser
# from pytube import Playlist
from spotipy.oauth2 import SpotifyOAuth

class YTtoSpotify:
	def __init__(self):

		# Configfile for the spotify credentials
		self.config = configparser.ConfigParser()
		self.config.read('spotifycreds.ini')
		self.username = self.config['default']['username']
		self.clientid = self.config['default']['id']
		self.clientsecret = self.config['default']['secret']

		# Asks the user for a youtube playlist link
		self.promptForList = input("Please enter the full playlist url (ex. https://www.youtube.com/playlist?list=[YOURPLAYLISTID]): ")
		self.playlist = pytube.Playlist(self.promptForList)
		self.done = False

		# Gets	the number of videos in the playlist
		self.urls = self.playlist.videos

		# Scope and auth of spotify
		self.scope = ['playlist-modify-public',
				'playlist-modify-private',
				'playlist-read-private',
				'playlist-read-collaborative',
				'user-library-modify',
				'user-library-read']
		
		# Spotify ID and the creation of a playlist
		try:
			self.spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.clientid, client_secret=self.clientsecret, redirect_uri='http://localhost:8080', scope=self.scope))
		except:
			print("Did you enter valid credentials?")
			exit()
		
		try:
			self.spotify.user_playlist_create(self.username, self.playlist.title, public=True)
		except:
			print("Did you enter a valid playlist url?")
			exit()

	# Get spotify ID of newly created playlist
	def getPlaylistID(self):
		self.newPlaylist = ""
		playlists = self.spotify.user_playlists(self.username)
		for item in playlists['items']:
			if item['name'] == f'{self.playlist.title}':
				self.newPlaylist = str(item['uri'])

	# A function that tries to clean up the names of the songs and artists before we do the search in spotify.
	def getCleanerTitles(self): 
		self.clean = []
		self.modified = []
		self.artistAndSong = []
		for url in self.urls:
			try:
				self.artistAndSong.append(f'{url.metadata[0]["Artist"]} - {url.metadata[0]["Song"]}') # If there is a song and artist name in the metadata, add these songs
			except:
				self.artistAndSong.append(f'{url.title}') # if the songname and artist doesn't exist in the metadata, just add the title
				self.modified.append(f'{url.title}') # in some cases, the cleaning below might erase too much, and because of that this will print the original titles later on incase we want to try searching for the songs ourselves
		for song in self.artistAndSong:
			self.clean.append(re.sub(r"\([^()]*\)|\[[^()]*\]", "", str(song))) # Deletes whatever is in parentheses and square brackets ex. (feat. hurrdurrmcstonk or ORIGINAL MUSIC VIDEO etc.) for somewhat more accurate searches

	# Add the songs to the new playlist
	def addSongs(self):
		self.ignoredSongs = []
		self.skipped = 0
		toBeAdded = []
		self.added = 0
		for song in self.clean:				
			try:
				songSearch = self.spotify.search(q=f'{song}', type="track")   # Searches spotify for the songs we've added to our list from Youtube
				toBeAdded.append(songSearch['tracks']['items'][0]['id']) # Adds succesful searches to a list
				self.added += 1	
			except:			
				self.skipped += 1 # Counts all the failed searches
				self.ignoredSongs.append(song.encode('utf-8', errors='replace')) # Adds the failed searches to a list
				pass # Next iteration
		while toBeAdded:
			self.spotify.user_playlist_add_tracks(self.username, playlist_id=f'{self.newPlaylist}', tracks=toBeAdded[:100]) # Adds the first 100 succesful songs to the new playlist
			toBeAdded = toBeAdded[100:] # Makes sure we add all the songs after 100 to the playlist

	# This is our starter, this starts all of our functions and sends a couple of messages
	def main(self):



		print(f'There is {len(self.urls)} videos in this playlist.')
		print('\n[!!!] This might take a while please wait. [!!!]')

		self.getPlaylistID()
		self.getCleanerTitles()
		self.addSongs()
		
		time.sleep(0.2)
		self.done = True
		time.sleep(1)

		print(f"\n\n[!!!] {self.added} out of {len(self.urls)} songs was successfully added to the playlist [!!!]")

		print(f"\n[!!!] {self.skipped} song(s) was skipped [!!!]: ") # Prints the songs that couldn't be added automatically
		for ignored in self.ignoredSongs:
			print(ignored)

		print("\n[!!!] These songs where modified [!!!]: ") # Prints all the songs where the title was modified in case some songs are missing
		for mod in self.modified:
			print(mod)

if __name__ == '__main__':
	YTtoSpotify().main()