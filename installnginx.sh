
echo ">>> Initializing routing server"



echo "add repo for latest stable nginx"
sudo add-apt-repository -y ppa:nginx/stable

echo "run apt-get update"
sudo apt-get --yes --force-yes update

echo "check if nginx is installed"
if [ ! -x /usr/sbin/nginx ]
then 
	echo "nginx is not installed, install now

	echo "install Nginx (-qq implies -y --force-yes)"
	sudo apt-get install -qq nginx
fi


echo "check if git is installed"
if [ ! -x /usr/bin/git ]
then 
	echo "git is not installed, install now"

	sudo apt-get --yes --force-yes install git
else
	echo "git is installed"
fi



# clone nginx config repo
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

echo "removing default server if exists"
sudo rm -fr /etc/nginx/sites-available/default
echo "removing default server if exists"

# place nginx config file
sudo rm /etc/nginx/nginx.conf
sudo mv nginx.conf /etc/nginx/

sudo service nginx restart
