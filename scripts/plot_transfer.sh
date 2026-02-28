#!/bin/bash
#scp $HOME/plots/*js geoscents.net:~/plots/
#scp $HOME/plots/*html geoscents.net:~/plots/
#scp $HOME/plots/*css geoscents.net:~/plots/
#scp $HOME/plots/*jpg geoscents.net:~/plots/
#for i in $HOME/plots/*.gif; do
#    [ -f "$i" ] || break
#    [[ $(find $i -type f -size +1000000c 2>/dev/null) ]] && echo "compress $i" && gifsicle -i $i -O3 --colors 256 -o $i || echo "$i already compressed!"
#done
#scp $HOME/plots/*gif geoscents.net:~/plots/

rsync -avzh $HOME/plots/flags/* root@geoscents.net:~/plots/flags/
rsync -avzh $HOME/plots/*js root@geoscents.net:~/plots/
rsync -avzh $HOME/plots/*html root@geoscents.net:~/plots/
rsync -avzh $HOME/plots/*css root@geoscents.net:~/plots/
rsync -avzh $HOME/plots/*jpg root@geoscents.net:~/plots/
rsync -avzh $HOME/plots/*png root@geoscents.net:~/plots/
rsync -avzh $HOME/plots/growth.png root@geoscents.net:~/plots/
rsync -avzh $HOME/geoscents/resources/maps/*_terrain.png root@geoscents.net:~/plots/
#rsync -avzh $1/plots/*gif geoscents.net:~/plots/

