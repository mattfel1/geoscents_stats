# Statistics for GeoScents Game

Game is hosted at http://geoscents.net.
Code for game is at https://github.com/mattfel1/geoscents.

This repository contains statistics for each city in the game, organized by map.  The JSON object is as follows:

* Entry: City/Country name
  * dists: List of players' geographic error, in km
  * times: List of players' click timestamp, in s (i.e. how much time was left on the 10s timer when player clicked)
  * regions: List of players' regions based on an IP lookup
  * countries: List of players' countries based on an IP lookup
  * mean_dist: Mean of dists
  * std_dist: Standard deviation of dists
  * mean_time: Mean of times
  * std_time: Standard deviation of times
  
