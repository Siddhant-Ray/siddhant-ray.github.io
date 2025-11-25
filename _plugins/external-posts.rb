require 'feedjira'
require 'httparty'
require 'jekyll'

module ExternalPosts
  class ExternalPostsGenerator < Jekyll::Generator
    safe true
    priority :high

    def generate(site)
      sources = site.config['external_sources']
      return if sources.nil?

      sources.each do |src|
        Jekyll.logger.info "ExternalPosts:", "Fetching external posts from #{src['name']}"

        begin
          response = HTTParty.get(src['rss_url'], timeout: 10)
          xml = response.body

          # Debug if CI returns HTML or wrong content
          if xml.strip.start_with?('<html', '<!DOCTYPE html')
            Jekyll.logger.warn "ExternalPosts:",
              "Feed #{src['rss_url']} returned HTML instead of RSS/Atom (likely blocked in CI)"
            next
          end

          feed = Feedjira.parse(xml)

        rescue Feedjira::NoParserAvailable
          snip = xml.to_s[0..200].gsub("\n", " ")
          Jekyll.logger.warn "ExternalPosts:",
            "No parser available for #{src['rss_url']}. First 200 chars: #{snip}"
          next

        rescue => e
          Jekyll.logger.warn "ExternalPosts:",
            "Error fetching #{src['rss_url']}: #{e.class} - #{e.message}"
          next
        end

        # Skip if no entries
        next if feed.nil? || feed.entries.nil?

        feed.entries.each do |e|
          Jekyll.logger.info "ExternalPosts:", "...Processing #{e.url}"

          slug = e.title.downcase.strip.gsub(' ', '-').gsub(/[^\w-]/, '')

          path = site.in_source_dir("_posts/#{slug}.md")

          doc = Jekyll::Document.new(
            path,
            site: site,
            collection: site.collections['posts']
          )

          doc.data['external_source'] = src['name']
          doc.data['feed_content'] = e.content
          doc.data['title'] = e.title.to_s
          doc.data['description'] = e.summary
          doc.data['date'] = e.published
          doc.data['redirect'] = e.url

          site.collections['posts'].docs << doc
        end
      end
    end
  end
end
