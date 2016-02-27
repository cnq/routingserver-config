
#!/bin/bash


sudo apt-get --yes --force-yes update

# install git
apt-get --yes --force-yes install git


echo "gitting repo $1 and checking out branch $2"

if [ -d /opt/config ]
then
        echo "repo exists, check out branch $2 and pull"
        git -C /opt/config checkout $2
        git -C /opt/config pull
else
        echo "cloning repo $1 and checking out branch $2"
        git clone -b $2 $1 /opt/config
fi


