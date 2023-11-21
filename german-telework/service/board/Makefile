NAME=board
FPC=fpc
#FPCFLAGS=-Fl/usr/lib/gcc/x86_64-redhat-linux/13
FPCFLAGS=-g
BUILDDIR=build

.PHONY: default clean
default: $(BUILDDIR)/$(NAME)
clean:
	rm -rf $(BUILDDIR)

$(BUILDDIR):
	mkdir -p $(BUILDDIR)
$(BUILDDIR)/$(NAME): src/main.pp src/boardtypes.pp src/boardserverthread.pp src/boardmessagestorage.pp src/transportcrypt.pp | $(BUILDDIR)
	$(FPC) -o$@ $(FPCFLAGS) $<
