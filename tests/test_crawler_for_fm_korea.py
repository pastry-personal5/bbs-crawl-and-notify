import unittest
from unittest.mock import MagicMock, patch
from selenium.common.exceptions import WebDriverException
from bbs_crawl_and_notify.crawler_for_fm_korea import visit_page, remove_urls, remove_video_tag_message

class TestVisitPage(unittest.TestCase):
    @patch("bbs_crawl_and_notify.crawler_for_fm_korea.logger")
    @patch("bbs_crawl_and_notify.crawler_for_fm_korea.sys")
    def test_visit_page_success(self, mock_sys, mock_logger):
        # Mock the Chrome driver
        mock_driver = MagicMock()
        mock_url = "https://www.example.com"

        # Call the function
        class TestVisitPage(unittest.TestCase):
            @patch("bbs_crawl_and_notify.crawler_for_fm_korea.logger")
            @patch("bbs_crawl_and_notify.crawler_for_fm_korea.sys")
            def test_visit_page_success(self, mock_sys, mock_logger):
                # Mock the Chrome driver
                mock_driver = MagicMock()
                mock_url = "https://www.example.com"

                # Call the function
                visit_page(mock_driver, mock_url)

                # Assert that driver.get was called with the correct URL
                mock_driver.get.assert_called_once_with(mock_url)

                # Ensure no errors were logged or sys.exit was called
                mock_logger.error.assert_not_called()
                mock_sys.exit.assert_not_called()

            @patch("bbs_crawl_and_notify.crawler_for_fm_korea.logger")
            @patch("bbs_crawl_and_notify.crawler_for_fm_korea.sys")
            def test_visit_page_webdriver_exception(self, mock_sys, mock_logger):
                # Mock the Chrome driver
                mock_driver = MagicMock()
                mock_driver.get.side_effect = WebDriverException("Test exception")
                mock_url = "https://www.example.com"

                # Call the function
                with self.assertRaises(SystemExit):
                    visit_page(mock_driver, mock_url)

                # Assert that driver.get was called with the correct URL
                mock_driver.get.assert_called_once_with(mock_url)

                # Ensure errors were logged and sys.exit was called
                mock_logger.error.assert_called()
                mock_sys.exit.assert_called_once_with(-1)


        class TestUtilityFunctions(unittest.TestCase):
            def test_remove_urls(self):
                text_with_urls = "Check this out: https://example.com and http://test.com"
                expected_result = "Check this out:  and "
                self.assertEqual(remove_urls(text_with_urls), expected_result)

            def test_remove_video_tag_message(self):
                text_with_message = "Video 태그를 지원하지 않는 브라우저입니다. Some other text."
                expected_result = " Some other text."
                self.assertEqual(remove_video_tag_message(text_with_message), expected_result)


        if __name__ == "__main__":
            unittest.main()
