This is a test note, that I am currently using to test if the Manifest file is being used during a deploy. TL:DR - working now! I needed to update the Github Actions steps to include caching the relevant files, so that the manifest and artifacts can actually be compared during the next deploy

Example of the Github Actions CI during a deploy

![[2026-11-24 Testing Prod Manifest File.webp]]

> [!info]
> The warnings have also been addressed FYI ![[good-news-everyone.gif]]


Update (2026-11-25): The manifest should not include an attribute `changed_this_run` if it is different between this and the previous manifest. Ideally, I should be able to quickly see what is new just by looking at the manifest! Can be shown nicely here:

![[2026-11-24 Testing Prod Manifest File docker.webp]]

![[2026-11-24 Testing Prod Manifest File json.webp]]
