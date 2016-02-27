#!/bin/bash


echo ">>> Initializing routing server"

echo "check if nginx is installed"
if [ ! -x /usr/sbin/nginx ]
then
        echo "nginx is not installed, install now"

        echo "add repo for latest stable nginx"
        sudo add-apt-repository -y ppa:nginx/stable

        echo "run apt-get update"
        sudo apt-get --yes --force-yes update

        echo "install nginx"
        #-qq implies -y --force-yes
        sudo apt-get install -qq nginx
else
        echo "nginx is installed, skipping install"
fi

echo "check if git is installed"
if [ ! -x /usr/bin/git ]
then
        echo "git is not installed, install now"

        sudo apt-get --yes --force-yes install git
else
        echo "git is installed, skipping install"
fi

# clone nginx config repo
echo "gitting repo $1 and checking out branch $2"

if [ -d /opt/conf ]
then
        echo "repo exists, check out branch $2 and pull"
        git -C /opt/conf checkout $2
        git -C /opt/conf pull
else
        echo "cloning repo $1 and checking out branch $2"
        git clone -b $2 $1 /opt/conf
fi

echo "removing default server if exists"
sudo rm -fr /etc/nginx/sites-available/default

echo "deploy nginx config"
sudo cp -R /opt/conf/*.conf /etc/nginx

echo "restart nginx"
sudo service nginx restart
