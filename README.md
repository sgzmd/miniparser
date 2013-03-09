MINIparser
===========

One day after a MINI which I was so going to buy tomorrow was gone from a dealer just because someone was quicker than me, I decided it has to stop. So next Saturday I made myself a cup of coffee and started thinking: I want to be notified as soon as new MINI pops up on their website. I do not want to check their website every morning. Therefore, I need to write a program which would do just that.

My first idea was to use `BeautifulSoup` - a great HTML parsing library for Python. Well, to cut a long story short, it didn't work - MINI's website was too smart for it's own good - it only presented proper results in the browser.

Browser it wants, I thought? Browser it will get - and installed selenium.

I started with recording a simple script in Selenium IDE - their Firefox extension which converted my clicks into their scripting language constructs. After exporting produced data as Python unit test, I spent some time cleaning it up and making sure that it, in fact, works.

My final step was exporting all extracted data to HTML format and sending an email - using GMail's SMTP server - and setting it up on cron. One little step left though is only sending new cars, i.e. those which were added since the last run.



