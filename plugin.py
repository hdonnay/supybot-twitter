###
# Copyright (c) 2007-2012, Andy Berdan, Alex Schumann, Henry Donnay
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks
from supybot import ircmsgs
from string import *

import twitter
from urllib2 import URLError, HTTPError

class Twitter(callbacks.Plugin):
    "Use !post to post messages via the associated twitter account."
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Twitter, self)
        self.__parent.__init__(irc)
        self.irc = irc
        self.mentionSince = None
        try:
            schedule.removeEvent('Mentions')
        except KeyError:
            pass
        t_consumer_key = self.registryValue('consumer_key')
        t_consumer_secret = self.registryValue('consumer_secret')
        t_access_key = self.registryValue('access_key')
        t_access_secret = self.registryValue('access_secret')
        self.api = twitter.Api(consumer_key=t_consumer_key, consumer_secret=t_consumer_secret, access_token_key=t_access_key, access_token_secret=t_access_secret)
        if self.registryValue('displayReplies'):
            statuses = self.api.GetMentions()
            self.mentionSince = statuses[0].id
            def mentionCaller():
                self._mention(irc)
            schedule.addPeriodicEvent(mentionCaller, 300, 'Mentions')

    def _mention(self, irc):
        statuses = self.api.GetMentions(since_id=self.mentionSince)
        if len(statuses) > 0:
            self.mentionSince = statuses[0].id
            for channel in self.registryValue('channelList').split():
                irc.queueMsg(ircmsgs.privmsg(channel, self.registryValue('replyAnnounceMsg')))
                for status in statuses:
                    msg = status.user.screen_name + ' -- ' + status.text
                    irc.queueMsg(ircmsgs.privmsg(channel, msg))
                    irc.noReply()

    def mentions(self, irc, msg, args, number):
        """<number>

        Displays latest <number> mentions"""
        statuses = self.api.GetMentions()
        for status in statuses[:number]:
            irc.reply(status.user.screen_name + ' -- ' + status.text)
    mentions = wrap(mentions, ['positiveInt'])

    def listfriends(self, irc, msg, args):
        """takes no arguments

        Echoes the friends list."""
        users = self.api.GetFriends()
        irc.reply( utils.str.format("%L", [u.screen_name for u in users] ) )
    listfriends = wrap(listfriends)

    def post(self, irc, msg, args, text):
        """<text>

        Posts <text> to the twitter network.
        """
        channel = msg.args[0]
        if not self.registryValue('enabled', channel):
            return
        try:
            self.api.PostUpdate( utils.str.format("%s (%s)", text, msg.nick) )
        except HTTPError:
            irc.reply( "HTTP Error... it may have worked..." )
        except URLError:
            irc.reply( "URL Error... it may have worked..." )
        else:
            irc.reply( self.registryValue('postConfirmation') )
    post = wrap(post, ['text'])

    def tweets(self, irc, msg, args):
        """takes no arguments

        Echoes the friends timeline.
        """
        statuses = self.api.GetFriendsTimeline()
        status_strs = ['%s (%s)' % (s.text, s.user.screen_name) for s in statuses]
        irc.reply(" || ".join(status_strs))
    tweets = wrap(tweets)

Class = Twitter
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
