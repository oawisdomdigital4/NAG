from rest_framework.decorators import api_view
from rest_framework.response import Response
from bs4 import BeautifulSoup
import requests
import re


@api_view(['GET', 'POST'])
def fetch_link_preview(request):
    # Accept url via POST body (`url`) or GET query param (`url`) so the
    # frontend composer can call GET /api/community/link-preview/?url=...
    url = None
    if request.method == 'GET':
        url = request.query_params.get('url')
    else:
        url = request.data.get('url')

    if not url:
        return Response({'error': 'URL is required'}, status=400)

    try:
        # Make request with timeout
        response = requests.get(url, timeout=5, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Get meta data
        title = (
            soup.find('meta', property='og:title')
            or soup.find('meta', property='twitter:title')
            or soup.find('title')
        )
        title = title.get('content', '') if hasattr(title, 'get') else title.string if title else ''
        
        description = (
            soup.find('meta', property='og:description')
            or soup.find('meta', property='twitter:description')
            or soup.find('meta', {'name': 'description'})
        )
        description = description.get('content', '') if description else ''
        
        image = (
            soup.find('meta', property='og:image')
            or soup.find('meta', property='twitter:image')
        )
        image = image.get('content', '') if image else ''
        
        # If no meta image, try to find first image
        if not image and soup.find('img'):
            images = soup.find_all('img', src=True)
            for img in images:
                src = img.get('src', '')
                if src and not re.match(r'^data:', src):
                    if not src.startswith('http'):
                        # Convert relative URL to absolute
                        image = requests.compat.urljoin(url, src)
                    else:
                        image = src
                    break
        
        return Response({
            'title': title.strip(),
            'description': description.strip(),
            'image': image,
            'url': url
        })
        
    except requests.RequestException as e:
        return Response({
            'error': f'Failed to fetch URL: {str(e)}'
        }, status=400)
    except Exception as e:
        return Response({
            'error': f'Error processing URL: {str(e)}'
        }, status=500)