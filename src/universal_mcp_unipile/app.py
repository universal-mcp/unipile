import json
from typing import Any, Dict, Optional, Callable, Literal
from loguru import logger

from universal_mcp.applications.application import APIApplication
from universal_mcp.integrations import Integration

class UnipileApp(APIApplication):
    """
    Application for interacting with the LinkedIn API via Unipile.
    Handles operations related to chats, messages, accounts, posts, and user profiles.
    """

    def __init__(self, integration: Integration) -> None:
        """
        Initialize the LinkedinApp.

        Args:
            integration: The integration configuration containing credentials and other settings.
                         It is expected that the integration provides the 'x-api-key'
                         via headers in `integration.get_credentials()`, e.g.,
                         `{"headers": {"x-api-key": "YOUR_API_KEY"}}`.
        """
        super().__init__(name="unipile", integration=integration)
        
        self._base_url = None
        
    @property
    def base_url(self) -> str:
        """
        Get the base URL for the Unipile API.
        This is constructed from the integration's credentials.
        """
        if not self._base_url:
            credentials = self.integration.get_credentials()
            subdomain = credentials.get("subdomain")
            port = credentials.get("port")
            if not subdomain or not port:
                logger.error("UnipileApp: Missing 'subdomain' or 'port' in integration credentials.")
                raise ValueError("Integration credentials must include 'subdomain' and 'port'.")
            self._base_url = f"https://{subdomain}.unipile.com:{port}"
        return self._base_url
    
    @base_url.setter
    def base_url(self, base_url: str) -> None:
        """
        Set the base URL for the Unipile API.
        This is useful for testing or if the base URL changes.

        Args:
            base_url: The new base URL to set.
        """
        self._base_url = base_url
        logger.info(f"UnipileApp: Base URL set to {self._base_url}")

    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get the headers for Apollo API requests.
        Overrides the base class method to use X-Api-Key.
        """
        if not self.integration:
            logger.warning("ApolloApp: No integration configured, returning empty headers.")
            return {}
        
        credentials = self.integration.get_credentials()
        
        api_key = credentials.get("api_key") or credentials.get("API_KEY") or credentials.get("apiKey")
        
        if not api_key:
            logger.error("ApolloApp: API key not found in integration credentials for Apollo.")
            return { # Or return minimal headers if some calls might not need auth (unlikely for Apollo)
                "Content-Type": "application/json",
                "Cache-Control": "no-cache"
            }

        logger.debug("ApolloApp: Using X-Api-Key for authentication.")
        return {
            "x-api-key": api_key,
            "Content-Type": "application/json",
            "Cache-Control": "no-cache" # Often good practice for APIs
        }
        

    def list_all_chats(
        self,
        unread: Optional[bool] = None,
        cursor: Optional[str] = None,
        before: Optional[str] = None,  # ISO 8601 UTC datetime
        after: Optional[str] = None,   # ISO 8601 UTC datetime
        limit: Optional[int] = None,   # 1-250
        account_type: Optional[str] = None,
        account_id: Optional[str] = None,  # Comma-separated list of ids
    ) -> dict[str, Any]:
        """
        Lists all chats, with options to filter by unread status, pagination, date ranges, and account.

        Args:
            unread: Filter for unread chats only or read chats only.
            cursor: Pagination cursor for the next page of entries.
            before: Filter for items created before this ISO 8601 UTC datetime (exclusive).
            after: Filter for items created after this ISO 8601 UTC datetime (exclusive).
            limit: Number of items to return (1-250).
            account_type: Filter by provider (e.g., "linkedin").
            account_id: Filter by specific account IDs (comma-separated).

        Returns:
            A dictionary containing a list of chat objects and a pagination cursor.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, chat, list, messaging, api
        """
        url = f"{self.base_url}/api/v1/chats"
        params: dict[str, Any] = {}
        if unread is not None:
            params["unread"] = unread
        if cursor:
            params["cursor"] = cursor
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if account_type:
            params["account_type"] = account_type
        if account_id:
            params["account_id"] = account_id

        response = self._get(url, params=params)
        return response.json()

    def list_chat_messages(
        self,
        chat_id: str,
        cursor: Optional[str] = None,
        before: Optional[str] = None,  # ISO 8601 UTC datetime
        after: Optional[str] = None,   # ISO 8601 UTC datetime
        limit: Optional[int] = None,   # 1-250
        sender_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Lists all messages from a specific chat, with pagination and filtering options.

        Args:
            chat_id: The ID of the chat to retrieve messages from.
            cursor: Pagination cursor for the next page of entries.
            before: Filter for items created before this ISO 8601 UTC datetime (exclusive).
            after: Filter for items created after this ISO 8601 UTC datetime (exclusive).
            limit: Number of items to return (1-250).
            sender_id: Filter messages from a specific sender ID.

        Returns:
            A dictionary containing a list of message objects and a pagination cursor.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, chat, message, list, messaging, api
        """
        url = f"{self.base_url}/api/v1/chats/{chat_id}/messages"
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if sender_id:
            params["sender_id"] = sender_id

        response = self._get(url, params=params)
        return response.json()

    def send_chat_message(
        self,
        chat_id: str,
        text: str,
    ) -> dict[str, Any]:
        """
        Sends a message in a specific chat.

        Args:
            chat_id: The ID of the chat where the message will be sent.
            text: The text content of the message.
            attachments: Optional list of attachment objects to include with the message.

        Returns:
            A dictionary containing the ID of the sent message.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, chat, message, send, create, messaging, api
        """
        url = f"{self.base_url}/api/v1/chats/{chat_id}/messages"
        payload: dict[str, Any] = {"text": text}

        response = self._post(url, data=payload)
        return response.json()

    def retrieve_chat(
        self,
        chat_id: str,
        account_id: Optional[str] = None 
    ) -> dict[str, Any]:
        """
        Retrieves a specific chat by its Unipile or provider ID.

        Args:
            chat_id: The Unipile or provider ID of the chat.
            account_id: Mandatory if the chat_id is a provider ID. Specifies the account context.

        Returns:
            A dictionary containing the chat object details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, chat, retrieve, get, messaging, api
        """
        url = f"{self.base_url}/api/v1/chats/{chat_id}"
        params: dict[str, Any] = {}
        if account_id:
            params["account_id"] = account_id

        response = self._get(url, params=params)
        return response.json()

    def list_all_messages(
        self,
        cursor: Optional[str] = None,
        before: Optional[str] = None,  # ISO 8601 UTC datetime
        after: Optional[str] = None,   # ISO 8601 UTC datetime
        limit: Optional[int] = None,   # 1-250
        sender_id: Optional[str] = None,
        account_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Lists all messages across all chats, with pagination and filtering options.

        Args:
            cursor: Pagination cursor.
            before: Filter for items created before this ISO 8601 UTC datetime.
            after: Filter for items created after this ISO 8601 UTC datetime.
            limit: Number of items to return (1-250).
            sender_id: Filter messages from a specific sender.
            account_id: Filter messages from a specific linked account.

        Returns:
            A dictionary containing a list of message objects and a pagination cursor.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, message, list, all_messages, messaging, api
        """
        url = f"{self.base_url}/api/v1/messages"
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if before:
            params["before"] = before
        if after:
            params["after"] = after
        if limit:
            params["limit"] = limit
        if sender_id:
            params["sender_id"] = sender_id
        if account_id:
            params["account_id"] = account_id

        response = self._get(url, params=params)
        return response.json()

    def list_all_accounts(
        self,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,  # 1-259 according to spec
    ) -> dict[str, Any]:
        """
        Lists all linked accounts.

        Args:
            cursor: Pagination cursor.
            limit: Number of items to return (1-259).

        Returns:
            A dictionary containing a list of account objects and a pagination cursor.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, account, list, unipile, api, important
        """
        url = f"{self.base_url}/api/v1/accounts"
        params: dict[str, Any] = {}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit

        response = self._get(url, params=params)
        return response.json()

    def retrieve_account(
        self,
        account_id: str,
    ) -> dict[str, Any]:
        """
        Retrieves a specific linked account by its ID.

        Args:
            account_id: The ID of the account to retrieve.

        Returns:
            A dictionary containing the account object details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, account, retrieve, get, unipile, api, important
        """
        url = f"{self.base_url}/api/v1/accounts/{account_id}"
        response = self._get(url)
        return response.json()

    def list_user_posts(
        self,
        identifier: str,    # User or Company provider internal ID
        account_id: str,    # Account to perform the request from (REQUIRED)
        cursor: Optional[str] = None,
        limit: Optional[int] = None,  # 1-100 (spec says max 250)
        is_company: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Lists all posts for a given user or company identifier.

        Args:
            identifier: The entity's provider internal ID (LinkedIn ID).
            account_id: The ID of the Unipile account to perform the request from (REQUIRED).
            cursor: Pagination cursor.
            limit: Number of items to return (1-100, as per Unipile example, though spec allows up to 250).
            is_company: Boolean indicating if the identifier is for a company.

        Returns:
            A dictionary containing a list of post objects and pagination details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, list, user_posts, company_posts, content, api
        """
        url = f"{self.base_url}/api/v1/users/{identifier}/posts"
        params: dict[str, Any] = {"account_id": account_id}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
        if is_company is not None:
            params["is_company"] = is_company

        response = self._get(url, params=params)
        return response.json()

    def retrieve_own_profile(
        self,
        account_id: str,
    ) -> dict[str, Any]:
        """
        Retrieves the profile of the user associated with the given Unipile account_id.

        Args:
            account_id: The ID of the Unipile account to use for retrieving the profile (REQUIRED).

        Returns:
            A dictionary containing the user's profile details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, user, profile, me, retrieve, get, api
        """
        url = f"{self.base_url}/api/v1/users/me"
        params: dict[str, Any] = {"account_id": account_id}
        response = self._get(url, params=params)
        return response.json()

    def retrieve_post(
        self,
        post_id: str,
        account_id: str, 
    ) -> dict[str, Any]:
        """
        Retrieves a specific post by its ID.

        Args:
            post_id: The ID of the post to retrieve.
            account_id: The ID of the Unipile account to perform the request from (REQUIRED).

        Returns:
            A dictionary containing the post details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, retrieve, get, content, api, important
        """
        url = f"{self.base_url}/api/v1/posts/{post_id}"
        params: dict[str, Any] = {"account_id": account_id}
        response = self._get(url, params=params)
        return response.json()

    def list_post_comments(
        self,
        post_id: str,  
        account_id: str,  
        comment_id: Optional[str] = None, 
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Lists all comments from a specific post. Can also list replies to a specific comment.

        Args:
            post_id: The social ID of the post.
            account_id: The ID of the Unipile account to perform the request from (REQUIRED).
            comment_id: If provided, retrieves replies to this comment ID instead of top-level comments.
            cursor: Pagination cursor.
            limit: Number of comments to return. (OpenAPI spec shows type string, passed as string if provided).

        Returns:
            A dictionary containing a list of comment objects and pagination details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, comment, list, content, api
        """
        url = f"{self.base_url}/api/v1/posts/{post_id}/comments"
        params: dict[str, Any] = {"account_id": account_id}
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = str(limit)
        if comment_id:
            params["comment_id"] = comment_id

        response = self._get(url, params=params)
        return response.json()

    def create_post(
        self,
        account_id: str,
        text: str,
        mentions: Optional[list[dict[str, Any]]] = None,
        external_link: Optional[str] = None, 
    ) -> dict[str, Any]:
        """
        Creates a new post on LinkedIn.

        Args:
            account_id: The ID of the Unipile account that will author the post (added as query parameter).
            text: The main text content of the post.
            mentions: Optional list of dictionaries, each representing a mention.
                      Example: `[{"entity_urn": "urn:li:person:...", "start_index": 0, "end_index": 5}]`
            external_link: Optional string, an external URL that should be displayed within a card.

        Returns:
            A dictionary containing the ID of the created post.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, create, share, content, api, important
        """
        url = f"{self.base_url}/api/v1/posts"
        
        params: dict[str, str] = {
            "account_id": account_id,
            "text": text,
        }

        if mentions:
            params["mentions"] = mentions
        if external_link:
            params["external_link"] = external_link

        response = self._post(url, data=params)
        return response.json()

    def list_post_reactions(
        self,
        post_id: str,    
        account_id: str,
        comment_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Lists all reactions from a specific post or comment.

        Args:
            post_id: The social ID of the post.
            account_id: The ID of the Unipile account to perform the request from .
            comment_id: If provided, retrieves reactions for this comment ID.
            cursor: Pagination cursor.
            limit: Number of reactions to return (1-100, spec max 250).

        Returns:
            A dictionary containing a list of reaction objects and pagination details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, reaction, list, like, content, api
        """
        url = f"{self.base_url}/api/v1/posts/{post_id}/reactions"
        params: dict[str, Any] = {"account_id": account_id}
        if cursor:
            params["cursor"] = cursor
        if limit:
            params["limit"] = limit
        if comment_id:
            params["comment_id"] = comment_id

        response = self._get(url, params=params)
        return response.json()

    def create_post_comment(
        self,
        post_social_id: str,
        account_id: str,
        text: str , 
        comment_id: Optional[str] = None,  # If provided, replies to a specific comment
        mentions_body: Optional[list[dict[str, Any]]] = None
    ) -> dict[str, Any]:
        """
        Adds a comment to a specific post.

        Args:
            post_social_id: The social ID of the post to comment on.
            account_id: The ID of the Unipile account performing the comment.
            text: The text content of the comment (passed as a query parameter).
                  Supports Unipile's mention syntax like "Hey {{0}}".
            comment_id: Optional ID of a specific comment to reply to instead of commenting on the post.
            mentions_body: Optional list of mention objects for the request body if needed.

        Returns:
            A dictionary, likely confirming comment creation. (Structure depends on actual API response)

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, comment, create, content, api, important
        """
        url = f"{self.base_url}/api/v1/posts/{post_social_id}/comments"
        params: dict[str, Any] = {
            "account_id": account_id, 
            "text": text, 
        }
            
        if comment_id:
            params["comment_id"] = comment_id

        if mentions_body:
            params = {"mentions": mentions_body} 

        response = self._post(url, data=params) 

        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": response.status_code, "message": "Comment action processed."}

    def add_reaction_to_post(
        self,
        post_social_id: str,  
        reaction_type: Literal["like", "celebrate", "love", "insightful", "funny", "support"],   
        account_id: str, 
        comment_id: Optional[str] = None  
    ) -> dict[str, Any]:
        """
        Adds a reaction to a post or comment.
        The OpenAPI spec does not detail the request body. This method assumes 'post_social_id'
        (as 'post_id') and 'reaction_type' (as 'value') are in the JSON body.
        'account_id' is an optional query parameter.
        Verify request/response structure with official Unipile LinkedIn API documentation.

        Args:
            post_social_id: The social ID of the post or comment to react to.
            reaction_type: The type of reaction .
            account_id: Account ID of the Unipile account performing the reaction.
            comment_id: Optional ID of a specific comment to react to instead of the post.

        Returns:
            A dictionary, likely confirming the reaction. (Structure depends on actual API response)

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, reaction, create, like, content, api, important
        """
        url = f"{self.base_url}/api/v1/posts/reaction"
        
        params: dict[str, str] = {
            "account_id": account_id,
            "post_id": post_social_id,
            "reaction_type": reaction_type
        }
        
        if comment_id:
            params["comment_id"] = comment_id
            
        response = self._post(url, data=params)

        try:
            return response.json()
        except json.JSONDecodeError:
            return {"status": response.status_code, "message": "Reaction action processed."}

    def search_posts(
        self,
        account_id: str,
        cursor: Optional[str] = None,
        limit: Optional[int] = None,
        keywords: Optional[str] = None,
        sort_by: Optional[Literal["relevance", "date"]] = None,
        date_posted: Optional[Literal["past_day", "past_week", "past_month"]] = None,
        content_type: Optional[Literal["videos", "images", "live_videos", "collaborative_articles", "documents"]] = None,
        posted_by: Optional[Dict[str, Any]] = None,
        mentioning: Optional[Dict[str, Any]] = None,
        author: Optional[Dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Performs a search for posts on LinkedIn based on a variety of criteria.

        Args:
            account_id: The ID of the Unipile account to perform the search from (REQUIRED).
            cursor: Pagination cursor for the next page of entries.
            limit: Number of items to return (up to 50 for Classic search).
            keywords: Keywords to search for in the post.
            sort_by: How to sort the results, e.g., "relevance" or "date".
            date_posted: Filter posts by when they were posted.
            content_type: Filter by the type of content in the post.
            posted_by: Dictionary to filter by who posted (e.g., {"me": True}, {"member": ["MEMBER_ID"]}).
            mentioning: Dictionary to filter by who is mentioned (e.g., {"company": ["COMPANY_ID"]}).
            author: Dictionary to filter by author details (e.g., {"industry": ["INDUSTRY_ID"]}).

        Returns:
            A dictionary containing a list of post objects and pagination details.

        Raises:
            httpx.HTTPError: If the API request fails.

        Tags:
            linkedin, post, search, find, content, api, important
        """
        url = f"{self.base_url}/api/v1/linkedin/search"
        
        params: dict[str, Any] = {"account_id": account_id}
        if cursor:
            params["cursor"] = cursor
        if limit is not None:
            params["limit"] = limit
            
        payload: dict[str, Any] = {
            "api": "classic",
            "category": "posts"
        }
        
        if keywords:
            payload["keywords"] = keywords
        if sort_by:
            payload["sort_by"] = sort_by
        if date_posted:
            payload["date_posted"] = date_posted
        if content_type:
            payload["content_type"] = content_type
        if posted_by:
            payload["posted_by"] = posted_by
        if mentioning:
            payload["mentioning"] = mentioning
        if author:
            payload["author"] = author

        response = self._post(url, params=params, data=payload)
        return self._handle_response(response)

    def list_tools(self) -> list[Callable]:
        
        return [
            self.list_all_chats,
            self.list_chat_messages,
            self.send_chat_message,
            self.retrieve_chat,
            self.list_all_messages,
            self.list_all_accounts,
            self.retrieve_account,
            self.list_user_posts,
            self.retrieve_own_profile,
            self.retrieve_post,
            self.list_post_comments,
            self.create_post,
            self.list_post_reactions,
            self.create_post_comment,
            self.add_reaction_to_post,
            self.search_posts
        ]