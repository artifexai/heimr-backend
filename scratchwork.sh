chmod 400 .cert/heimr-admin.pem
#APP     3.21.245.13
ssh -i .cert/heimr-admin.pem ec2-user@ec2-3-21-245-13.us-east-2.compute.amazonaws.com
# Server 18.216.130.199
ssh -i .cert/heimr-admin.pem ec2-user@ec2-18-216-130-199.us-east-2.compute.amazonaws.com

# Install dependencies
sudo yum update
sudo yum update -y
sudo amazon-linux-extras install docker
sudo yum install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo yum install -y git
sudo yum install -y nginx

# Clone repo
git clone https://github.com/builtonml/heimr-backend.git
# shellcheck disable=SC2164
cd heimr-backend

# Create .env
sudo touch .env
sudo vim .env

# Edit your-side.conf
sudo vim /etc/nginx/conf.d/your-site.conf
# server {
  #    listen 80;
  #    server_name heimr.io;
  #location / {
  #        proxy_pass http://127.0.0.1:5000;
  #        proxy_set_header Host $host;
  #        proxy_set_header X-Real-IP $remote_addr;
  #        proxy_set_header X-Forwarded-For
  #$proxy_add_x_forwarded_for;
  #        proxy_set_header X-Forwarded-Proto $scheme;
  #} }

sudo systemctl restart nginx

# Create certificates
cd .. # exit heimr-backend
sudo python3 -m venv /opt/certbot/
sudo /opt/certbot/bin/pip install --upgrade pip
sudo /opt/certbot/bin/pip install certbot certbot-nginx
sudo ln -s /opt/certbot/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d server.heimr.io
#sudo certbot --nginx -d heimr.io -d www.heimr.io -d server.heimr.io
# matt@cogni-code.com,russ@artifexai.io,bertie@artifexai.io,Bojan@builtonml.com

# Start docker
sudo docker-compose up api
