#Install Virtual Box
sudo apt install virtualbox

#Install Vagrant
sudo apt install vagrant

#Setting up Virtual Box
sudo apt-get install linux-headers-generic
sudo dpkg-reconfigure virtualbox-dkms
sudo dpkg-reconfigure virtualbox
sudo modprobe vboxdrv
sudo modprobe vboxnetflt

vagrant up --provider virtualbox

