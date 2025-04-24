class LinkVisitorClientContext:
    driver = None  # It's a Selenium driver.

    def __init__(self):
        self.driver = None

    def clean_up(self):
        if self.driver:
            self.driver.quit()