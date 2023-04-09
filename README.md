# Statistics for GeoScents Game

GeoScents is an online multiplayer geography game.  You are given a city and you must try to click the city on the map as quickly and accurately as possible.  Scores are tracked along with the player's region and country.  The data is dumped here every each day for you to peruse and play with.  Feel free to open issues if you would like to see other statistics added to the dataset, and share any interesting results you find!

Game is hosted at http://geoscents.net.
Code for game is at https://github.com/mattfel1/geoscents.

This repository contains statistics for each city in the game, organized by map.  The JSON object is as follows:

* `Entry: String` - City/Country name as shown in game
  * `dists: Seq[Float]` - List of players' geographic error, in km
  * `times: Seq[Float]` - List of players' click timestamp, in s (i.e. how much time was left on the 10s timer when player clicked)
  * `regions: Seq[String]` - List of players' regions based on an IP lookup
  * `countries: Seq[String` - List of players' countries based on an IP lookup
  * `mean_dist: Float` - Mean of dists
  * `std_dist: Float` - Standard deviation of dists
  * `mean_time: Float` - Mean of times
  * `std_time: Float` - Standard deviation of times
  * `country: String` - Country 
  * `admin: String` - Administrative name of target city (i.e. State or province)
  * `city: String` - City name
  
The dists, times, regions, and countries lists are in-order (i.e. the n'th element in each correspond to a single guess by a player)

The file `metadata.json` reports basic statistics for what you will find in each map's json.  Specifically, it contains:
* `Entry: String` - Map name
  * `num_clicks: Int` - Number of unique click events for that map (i.e. one player making one guess adds one to this count)
  * `num_cities: Int` - Number of cities containing data for this map (should not change once all cities in the game have been played at least once)
  * `num_clicks_per_city: Float` - num_clicks / num_cities
  * `most_played_city: String` - City that has been played the most on this map
  * `must_played_city_num_clicks: Int` - Number of clicks for this most played city
