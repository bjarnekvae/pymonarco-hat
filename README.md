# pymonarco-hat
Python3 wrapper for Monarco HAT C drivers, see [Monarco driver repository](https://github.com/monarco/monarco-hat-driver-c)

## Getting started
Before you can use this wrapper you need to clone the [Monarco HAT Driver C repository](https://github.com/monarco/monarco-hat-driver-c):

Install git and build-dependencies on your Raspberry Pi running Raspbian:
<pre>
sudo apt update
sudo apt install git build-essential 
</pre>

Clone the Monarco HAT repository repository:
<pre>
cd ~
git clone https://github.com/monarco/monarco-hat-driver-c.git
</pre>

Clone this repository:
<pre>
cd ~
git clone https://github.com/bjarnekvae/pymonarco-hat.git
</pre>

## Build library
In order for the Python wrapper to work we need to build a library file from the Monarco HAT source code, this can be done like this:
<pre>
cd ~/pymonarco-hat/monarco-c
make MONARCO_PATH=/path/to/monarco-hat-driver-c-repository
</pre>

From this "libmonarco.so" will be compiled, this file will be used for the wrapper.

## Install wrapper 
Run:
<pre>
cd ~/pymonarco-hat
python3 setup.py install
</pre>

## Run example
<pre>
cd ~/pymonarco-hat/examples
python3 monarco_example.py
</pre>

In most cases the script has to be run as root, unless you've given your user right to access the SPI peripheral


## Note

- Counter functionality is not implemented (yet)

## Requirements

- Python 3.6 and above.

## License

Under MIT license. See [LICENSE](LICENSE).

## Authors

- Bjarne Kvæstad <bjarnekvae@gmail.com>