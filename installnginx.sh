
echo ">>> Installing Nginx"

# Add repo for latest stable nginx
sudo add-apt-repository -y ppa:nginx/stable

# Update Again
sudo apt-get update

# Install Nginx
# -qq implies -y --force-yes
sudo apt-get install -qq nginx

# place nginx config file
sudo rm /etc/nginx/nginx.conf
sudo mv nginx.conf /etc/nginx/

sudo service nginx restart