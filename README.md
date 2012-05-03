# gettext-js

This is a naïve hack to produce *gettext* compatible files from JavaScript. *xgettext* doesn't have support for the JavaScript language and the de-facto way of doing things seems to be applying some nasty regular expressions on the JS file and running it through xgettext as either Python or Perl.

I have found this method to be insufficient for the code I write. Thus, this nasty thing. Theoretically, it is just as crappy as the other way. However in practice it wins out because it is better maintainable, smaller, and runs as a pure-Python solution (a plus if that is your environment).

