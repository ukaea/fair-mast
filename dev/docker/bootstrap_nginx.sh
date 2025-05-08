echo Starting Nginx Config update;
cp /nginx_conf/default.conf /nginx_conf/temp.conf;
sed 's/self_signed/mastapp.site/g' /nginx_conf/temp.conf > /nginx_conf/default.conf;
rm /nginx_conf/temp.conf;
echo Finished Nginx Config Update;