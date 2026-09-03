# frozen_string_literal: true

Encoding.default_external = Encoding::UTF_8
Encoding.default_internal = Encoding::UTF_8

require "bibtex"
require "fileutils"
require "minitest/autorun"
require "nokogiri"
require "open3"
require "tmpdir"

class PublicationsRenderTest < Minitest::Test
  ROOT = File.expand_path("..", __dir__)
  BIBLIOGRAPHIES = {
    "preprints" => "preprints.bib",
    "peer reviewed" => "papers.bib",
    "posters" => "posters.bib"
  }.freeze

  class << self
    attr_reader :home, :publications, :stylesheet

    def build_site
      return if @publications

      @site_dir = Dir.mktmpdir("portfolio-site-")
      stdout, stderr, status = Open3.capture3(
        { "LANG" => "en_US.UTF-8", "LC_ALL" => "en_US.UTF-8" },
        "bundle", "exec", "jekyll", "build",
        "--config", [File.join(ROOT, "_config.yml"), File.join(ROOT, "test", "_config.yml")].join(","),
        "--destination", @site_dir,
        chdir: ROOT
      )

      raise "Jekyll build failed:\n#{stdout}\n#{stderr}" unless status.success?

      @home = Nokogiri::HTML(File.read(File.join(@site_dir, "index.html")))
      @publications = Nokogiri::HTML(
        File.read(File.join(@site_dir, "publications", "index.html"))
      )
      @stylesheet = File.read(File.join(@site_dir, "assets", "css", "main.css"))
    end

    def cleanup
      FileUtils.remove_entry(@site_dir) if @site_dir
    end
  end

  Minitest.after_run { cleanup }

  def setup
    self.class.build_site
  end

  def test_each_publication_section_has_descending_year_headings
    BIBLIOGRAPHIES.each do |section, filename|
      assert_equal expected_years(filename), rendered_years(section), section
    end
  end

  def test_publications_page_does_not_append_year_to_periodical
    BIBLIOGRAPHIES.each_value do |filename|
      bibliography(filename).each do |entry|
        periodical = self.class.publications.at_xpath(
          "//*[@id='#{entry.key}']/*[contains(concat(' ', normalize-space(@class), ' '), ' periodical ')]"
        )

        assert periodical, "missing periodical for #{entry.key}"
        assert_equal expected_periodical(entry), normalize(periodical.text), entry.key
      end
    end
  end

  def test_homepage_selected_publications_keep_inline_years
    bibliography("papers.bib").select { |entry| entry[:selected].to_s == "true" }.each do |entry|
      periodical = self.class.home.at_xpath(
        "//*[@id='#{entry.key}']/*[contains(concat(' ', normalize-space(@class), ' '), ' periodical ')]"
      )

      assert periodical, "missing selected publication #{entry.key}"
      assert_equal "#{expected_periodical(entry)} #{entry[:year]}", normalize(periodical.text), entry.key
    end
  end

  def test_year_heading_is_more_visible_than_its_panel_divider
    heading = css_declarations(".publications h2.bibliography")
    year_color_variable = css_variable_in(heading.fetch("color"))
    divider_color_variable = css_variable_in(heading.fetch("border-top"))

    [":root", "html[data-theme=dark]"].each do |theme_selector|
      theme = css_declarations(theme_selector)
      background = composite_color(theme.fetch("--global-bg-color"), [255, 255, 255])
      year_color = composite_color(theme.fetch(year_color_variable), background)
      divider_color = composite_color(theme.fetch(divider_color_variable), background)

      assert_operator contrast(year_color, background), :>, contrast(divider_color, background), theme_selector
    end
  end

  private

  def bibliography(filename)
    BibTeX.open(File.join(ROOT, "_bibliography", filename)).entries.values
  end

  def expected_years(filename)
    bibliography(filename).map { |entry| entry[:year].to_s }.uniq.sort.reverse
  end

  def expected_periodical(entry)
    venue = case entry.type.to_s
            when "article" then entry[:journal].to_s
            when "inproceedings" then "In #{entry[:booktitle]}"
            else ""
            end
    month = entry[:month].to_s

    normalize([venue, month.empty? ? nil : month.capitalize].compact.join(" "))
  end

  def rendered_years(section)
    heading = self.class.publications.css(".publications > h1").find do |element|
      normalize(element.text) == section
    end
    raise "missing section #{section}" unless heading

    years = []
    element = heading.next_element
    until element.nil? || element.name == "h1"
      years << normalize(element.text) if element.matches?("h2.bibliography")
      element = element.next_element
    end
    years
  end

  def normalize(text)
    text.gsub(/\s+/, " ").strip
  end

  def css_declarations(selector)
    block = self.class.stylesheet.match(/#{Regexp.escape(selector)}\s*\{([^}]+)\}/m)
    raise "missing CSS selector #{selector}" unless block

    block[1].scan(/([\w-]+):\s*([^;]+);/).to_h
  end

  def css_variable_in(value)
    value[/var\((--[\w-]+)\)/, 1] || raise("missing CSS variable in #{value}")
  end

  def composite_color(value, background)
    channels, alpha = if (hex = value.match(/\A#([0-9a-f]{6})\z/i))
                        [hex[1].scan(/../).map { |channel| channel.to_i(16) }, 1.0]
                      elsif (rgba = value.match(/\Argba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)\z/))
                        [rgba.captures.first(3).map(&:to_i), rgba[4].to_f]
                      else
                        raise "unsupported CSS color #{value}"
                      end

    channels.zip(background).map { |channel, base| channel * alpha + base * (1 - alpha) }
  end

  def contrast(first, second)
    lighter, darker = [luminance(first), luminance(second)].sort.reverse
    (lighter + 0.05) / (darker + 0.05)
  end

  def luminance(color)
    color.map do |channel|
      normalized = channel / 255.0
      normalized <= 0.04045 ? normalized / 12.92 : ((normalized + 0.055) / 1.055)**2.4
    end.zip([0.2126, 0.7152, 0.0722]).sum { |channel, weight| channel * weight }
  end
end
