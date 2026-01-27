FROM postgres:15.3

RUN apt update
RUN apt install wget -y

WORKDIR /tmp
RUN wget https://github.com/peak/s5cmd/releases/download/v2.3.0/s5cmd_2.3.0_Linux-64bit.tar.gz -O s5cmd.tar.gz
RUN mkdir s5cmd_unpack
RUN tar -xvzf s5cmd.tar.gz -C ./s5cmd_unpack
RUN cp ./s5cmd_unpack/s5cmd /usr/local/bin
RUN rm -rf s5cmd.tar.gz
RUN rm -rf ./s5cmd_unpack