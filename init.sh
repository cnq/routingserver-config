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

echo "check if nginx cache directory exists"
if [ ! -x /var/cache/nginx ]
then
        echo "creating nginx cache directory"

        mkdir /var/cache/nginx
else
        echo "nginx cache directory exists, skipping mkdir"
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
		git -C /opt/conf fetch origin
		git -C /opt/conf reset --hard origin/$2
        git -C /opt/conf checkout $2
else
        echo "cloning repo $1 and checking out branch $2"
        git clone -b $2 $1 /opt/conf
fi

echo "removing default server if exists"
sudo rm -fr /etc/nginx/sites-available/default

echo "deploy nginx config"
sudo cp -v -R /opt/conf/*.conf /etc/nginx
sudo cp -v -R /opt/conf/snippets/*.conf /etc/nginx/snippets

echo "restart nginx"
sudo service nginx restart
