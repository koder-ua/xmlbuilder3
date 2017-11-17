VERSION=1.0
NAME=xmlbuilder3
TARGET=dist/$(NAME)-$(VERSION).tar.gz
$(TARGET) : setup.py $(NAME)/* README.txt
		python setup.py sdist
