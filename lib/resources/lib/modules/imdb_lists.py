
from bs4 import BeautifulSoup as bss
from resources.lib.modules import (log_utils, client)

import re

class IMDBLists(object):
    """
    Representation of IMDB lists. Use this to fetch tv show and movie lists
    for a given imdb user id.
    """
    user_list_url = 'http://www.imdb.com/list/{listid}'
    users_url = 'http://www.imdb.com/user/ur{userid}/'
    search_url = 'http://www.imdb.com/search/title'
    # The total number of results to fetch
    results_count = 90

    def __init__(self, title_type, imdb_user=None):
        """
        Parameters:
        title_type: One of ['movie', 'tvSeries']. This is used to filter the list
        imdb_user:  The user id for the imdb account (numbers only). Only needed for
                    user lists.
        """
        assert title_type in ['movie', 'tvSeries']
        self.imdb_user = imdb_user
        self.title_type = title_type

    def params_encode(self, params):
        """
        Encode a dictionary into a string of URL parameters
        """
        return '&'.join(['{}={}'.format(k, v) for k, v in params.items()])

    def get_user_lists(self):
        """
        Return all the imdb lists for this user.
        """
        if not self.imdb_user:
            return []
        ulist = []
        url = self.users_url.format(userid=self.imdb_user)
        result = client.request(url)
        soup = bss(result, "html.parser")
        items = soup.findAll("div", { "class" : "user-list" })
        for item in items:
            list_id = item['id']
            list_name = item.find("a", {"class": "list-name"}).get_text()
            if self.title_type == 'tvSeries':
                url = ("q=imdbUserList&listId={}").format(list_id)
            else:
                url = ("q=imdbUserList&listId={}").format(list_id)
            ulist.append({'name': list_name, 'id': list_id, 'url': url, 'tvdb': '0'})
        return ulist

    def build_user_list_url(self, list_id, extra=None):
        """
        Build the imdb URL for fetching contents of a user list
        """
        if not self.imdb_user:
            raise("Must set imdb_user if calling imdb user list")
        params = {'sort': 'alpha,asc', 'mode': 'detail',
                  'title_type': self.title_type}
        url = '{}?{}'.format(self.user_list_url.format(listid=list_id),
                             self.params_encode(params))
        return url

    def build_imdb_list_url(self, list_type, params_extra=None, hidecinema=False):
        """
        Build the url for fetching imdb list contents
        """
        params = {'title_type': self.title_type,
                  'count': self.results_count,
                  'start': 1,
                 }
        if params_extra is not None:
            params = dict(params.items() + params_extra.items())

        if hidecinema:
            params.update('release_date',',date[90]')
        if list_type == 'popular':
            params.update({'num_votes': '1000,', 'sort': 'moviemeter,asc'})
        elif list_type == 'views':
            params.update({'num_votes': '1000,', 'sort': 'num_votes,desc'})
        elif list_type == 'featured':
            params.update({'release_date':'date[365]','num_votes': '1000,',
                           'sort': 'moviemeter,asc'})
        elif list_type == 'boxoffice':
            params.update({'num_votes': '1000,', 'sort': 'boxoffice_gross_us,desc'})
        elif list_type == 'oscars':
            params.update({'groups': 'oscar_best_picture_winners'})
        elif list_type == 'theater':
            params.update({'title_type': 'feature',
                'release_date': 'date[365],date[0]',
                'sort': 'release_date_us,desc'
                })
        elif list_type == 'premiertv':
            params.update({'num_votes': '10,',
                'release_date': 'date[60],date[0]',
                'sort': 'release_date,desc',
                'languages': 'en',
                })
        elif list_type == 'populartv':
            params.update({'num_votes': '100,',
                'release_date': ',date[0]',
                'sort': 'moviemeter,asc',
                })
        elif list_type == 'ratingtv':
            params.update({'num_votes': '5000,',
                'release_date': ',date[0]',
                'sort': 'user_rating,desc',
                })
        elif list_type == 'ratingtv':
            params.update({'num_votes': '5000,',
                'release_date': ',date[0]',
                'sort': 'user_rating,desc',
                })
        elif list_type == 'airingtv':
            params.update({'title_type': 'tv_episodes',
                'release_date': 'date[1],date[0]',
                'sort': 'moviemeter,asc',
                })
        elif list_type == 'viewstv':
            params.update({'num_votes': '100',
                'release_date': ',date[0]',
                'sort': 'num_votes,desc',
                })
        else:
            log_utils.log("{} didn't match any of our options.".format(list_type))
            return []
        params_enc = self.params_encode(params)
        url = "{}?{}".format(self.search_url, params_enc)
        return url

    def build_imdb_search_url(self, params, hidecinema=True):
        """
        Build a custom imdb search url using params
        """
        default_params = {'count': self.results_count, 'start': 1}
        p = dict(default_params.items() + params.items())
        return "{}?{}".format(self.search_url, self.params_encode(p))

    def get_imdb_url_contents(self, url):
        """
        Retrieve the list of shows for the given url
        """
        if not url:
            return []
        results_list = []
        result = client.request(url)
        soup = bss(result, "html.parser")
        for li in soup.findAll("div", {"class": "lister-item"}):
            title = li.find("h3", {"class": "lister-item-header"}).find('a').getText()
            year_raw = li.find("span", {"class": "lister-item-year"}).getText()
            year = int(re.search('(\d+)', year_raw).group(0))
            try:
                rating = li.find("div", {"class": "ratings-imdb-rating"}).find("strong").get_text()
            except:
                rating = '?'
            plot = li.find("p", {"class": ""}).getText().strip()
            imdb = li.find("div", {"class": "lister-item-image"}).find("img")['data-tconst']
            poster = li.find("div", {"class": "lister-item-image"}).find("img")['loadlate']
            results_list.append({
                    'title': title,
                    'originaltitle': title,
                    'year': year,
                    'rating': rating,
                    'plot': plot,
                    'imdb': imdb,
                    'poster': poster,
                    'tvdb': '0',
                })
        return results_list

    def get_user_list_contents(self, list_id):
        """
        Get the contents of the user list given by list_id
        """
        url = self.build_user_list_url(list_id)
        return self.get_imdb_url_contents(url)

    def get_imdb_list_contents(self, list_type, hidecinema=False):
        """
        Get the contents of the imdb list by type
        """
        url = self.build_imdb_list_url(list_type, hidecinema=False)
        return self.get_imdb_url_contents(url)
