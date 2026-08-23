I am working on doing a build cache via a Manifest file to improve publication

<!--more-->

Instead of deleting the entire `site_src` directory and then re-copying, I am instead using a cache strategy. If the `sha256` of a file changed, the `name` of the file changed or the file was deleted - only then should it be updated in the remote destination - the rest remains as is.