# Code for running GnuPG in batch mode and dealing with the results

__rcsid__ = '$Id: GPG.py,v 1.1.1.1 2000/04/17 02:17:24 amk Exp $'

import os, string
import cStringIO, popen2

class Signature:
    "Class used to hold information about a signature result"

    def __init__(self):
        self.valid = 0
        self.fingerprint = self.creation_date = self.timestamp = None
        self.signature_id = self.key_id = None
        self.username = None
        
    def is_valid(self):
        return self.valid
    
class GPGSubprocess:

    # Default path used for searching for the GPG binary, when the
    # PATH environment variable isn't set.
    DEFAULT_PATH = ['/bin', '/usr/bin', '/usr/local/bin']
    
    def __init__(self, gpg_binary = None):
        """Initialize an object instance.  Options are:

        gpg_binary -- full pathname for GPG binary.  If not supplied,
        the current value of PATH will be searched, falling back to the
        DEFAULT_PATH class variable if PATH isn't available.
        """

        # If needed, look for the gpg binary along the path
        if gpg_binary is None:
            import os
            if os.environ.has_key('PATH'):
                path = os.environ['PATH']
                path = string.split(path, os.pathsep)
            else:
                path = self.DEFAULT_PATH

            for dir in path:
                fullname = os.path.join(dir, 'gpg')
                if os.path.exists( fullname ):
                    gpg_binary = fullname
                    break
            else:
                raise ValueError, ("Couldn't find 'gpg' binary on path"
                                   + repr(path) )
            
        self.gpg_binary = gpg_binary

    def verify(self, data):
        "Verify the signature on the contents of the string 'data'"
        file = cStringIO.StringIO( data )
        return self.verify_file( file )
    
    def verify_file(self, file):
        "Verify the signature on the contents of the file-like object 'file'"
        child_stdout, child_stdin, child_stderr = self._open_subprocess()

        # Copy the file to the GPG subprocess
        while 1:
            data = file.read(1024)
            if data == "": break
            child_stdin.write(data)

        child_stdin.close()
        
        # Get the response information
        resp = self._read_response(child_stderr)

        # Create an object to return, and fill it with data
        sig = Signature()
        if resp.has_key('BADSIG'):
            sig.valid = 0
            sig.key_id, sig.username = string.split(resp['BADSIG'], None, 1)
        elif resp.has_key('GOODSIG'):
            sig.valid = 1
            sig.key_id, sig.username = string.split(resp['GOODSIG'], None, 1)

        if resp.has_key('VALIDSIG'):
            L = string.split(resp['VALIDSIG'], None)
            sig.fingerprint, sig.creation_date, sig.timestamp = L

        if resp.has_key('SIG_ID'):
            L = string.split(resp['SIG_ID'], None)
            sig.signature_id, sig.creation_date, sig.timestamp = L

        # Read the contents of the file from GPG's stdout
        sig.data = ""
        while 1:
            data = child_stdout.read(1024)
            if data == "": break
            sig.data = sig.data + data
            
        return sig
    
    def _open_subprocess(self, *args):
        # Internal method: open a pipe to a GPG subprocess and return
        # the file objects for communicating with it.

        cmd = self.gpg_binary + ' --status-fd 2 ' + string.join(args)
        
        child_stdout, child_stdin, child_stderr = popen2.popen3(cmd)
        return child_stdout, child_stdin, child_stderr

    def _read_response(self, child_stdout):
        # Internal method: reads all the output from GPG, taking notice
        # only of lines that begin with the magic [GNUPG:] prefix.
        # (See doc/DETAILS in the GPG distribution for info on GPG's
        # output when --status-fd is specified.)
        #
        # Returns a dictionary, mapping GPG's keywords to the arguments
        # for that keyword.
        
        resp = {}
        while 1:
            line = child_stdout.readline()
            if line == "": break
            line = string.rstrip( line )
            if line[0:9] == '[GNUPG:] ':
                # Chop off the prefix
                line = line[9:]
                L = string.split(line, None, 1)
                keyword = L[0]
                if len(L) > 1:
                    resp[ keyword ] = L[1]
                else:
                    resp[ keyword ] = ""
        return resp
    

    # Not yet implemented, because I don't need these methods
    # The methods certainly don't have all the parameters they'd need.
    
    def sign(self, data):
        "Sign the contents of the string 'data'"
        pass

    def sign_file(self, file):
        "Sign the contents of the file-like object 'file'"
        pass

    def encrypt_file(self, file):
        "Encrypt the message read from the file-like object 'file'"
        pass

    def encrypt(self, data):
        "Encrypt the message contained in the string 'data'"
        pass

    def decrypt_file(self, file):
        "Decrypt the message read from the file-like object 'file'"
        pass

    def decrypt(self, data):
        "Decrypt the message contained in the string 'data'"
        pass

    
if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        print 'Usage: GPG.py <signed file>'
        sys.exit()

    obj = GPGSubprocess()
    file = open(sys.argv[1], 'rb')
    sig = obj.verify_file( file )
    print sig.__dict__

