import pytest
from news_fetcher import clean_news_text, fetch_article, reject_non_article_page


def test_google_news_home_is_not_an_article():
    with pytest.raises(ValueError, match="Google News feed"):
        reject_non_article_page("https://news.google.com/home?hl=en-IN&gl=IN&ceid=IN:en")


def test_google_news_search_is_not_an_article():
    with pytest.raises(ValueError, match="Google News feed"):
        reject_non_article_page("https://news.google.com/search?q=technology")


def test_non_news_root_homepage_is_rejected():
    with pytest.raises(ValueError, match="website homepage"):
        reject_non_article_page("https://example.com/")


def test_article_path_is_accepted_by_homepage_guard():
    reject_non_article_page("https://example.com/news/local-story-123")


def test_html_entities_and_whitespace_cleaned():
    assert clean_news_text("News&nbsp; today \n\t &amp; more") == "News today & more"
