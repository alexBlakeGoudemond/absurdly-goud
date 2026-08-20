FROM ruby:3.3

# Install Python (for the Obsidian converter) and basic utilities
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-pip ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /site

# Copy Gemfiles and install gems at image build time to avoid long startup
COPY Gemfile Gemfile.lock /site/
RUN bundle config set --local path /usr/local/bundle \
 && bundle install --jobs 4 --retry 3 || true

# Copy entrypoint into image (volume mount will override /site at runtime but not /usr/local/bin)
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
