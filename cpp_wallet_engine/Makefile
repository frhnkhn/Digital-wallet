# Makefile for C++ Wallet Engine
# Compiles all C++ sources -> libwallet.so (shared library for Python ctypes)

CXX      = g++
CXXFLAGS = -Wall -Wextra -O2 -fPIC -std=c++17

TARGET   = libwallet.so
SRCS     = Transaction.cpp Wallet.cpp User.cpp AdminUser.cpp \
           WalletEngine.cpp wallet_c_api.cpp
HDRS     = Entity.h Transaction.h Wallet.h User.h AdminUser.h \
           WalletEngine.h wallet_c_api.h

all: $(TARGET)

$(TARGET): $(SRCS) $(HDRS)
	$(CXX) $(CXXFLAGS) -shared -o $(TARGET) $(SRCS)
	@echo "✅ Built $(TARGET) successfully"

clean:
	rm -f $(TARGET) *.o

.PHONY: all clean
