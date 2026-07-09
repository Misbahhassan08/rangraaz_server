import json

from .models import CustomPage, HeaderGroup, PageBlock, Products


class PageBuilderService:
    """Page CMS serializer and writer used by the public page APIs."""

    @staticmethod
    def product_to_dict(product):
        first_image = product.images.first()
        return {
            'id': product.id,
            'product_name': product.product_name,
            'category': product.category.name if product.category else 'N/A',
            'category_id': product.category_id,
            'sub_category': product.subcategory.name if product.subcategory else 'N/A',
            'subcategory_id': product.subcategory_id,
            'sub_subcategory': product.sub_subcategory.name if product.sub_subcategory else 'N/A',  # ← ADD
            'sub_subcategory_id': product.sub_subcategory_id,
            'original_price': product.original_price,
            'sell_price': product.sell_price,
            'discount_percentage': product.discount_percentage,
            'is_sale_on': product.is_sale_on,
            'quantity': product.quantity,
            'image_url': first_image.image.url if first_image else '',
            'images': [
                {'id': img.id, 'image_url': img.image.url, 'order': img.order}
                for img in product.images.all()
            ],
            'size_stocks': [
                {'size': ss.size, 'quantity': ss.quantity}
                for ss in product.size_stocks.all()
            ],
            'sku': product.sku,
            'vendor': product.vendor,
            'product_type': product.product_type,
        }

    @classmethod
    def serialize_page(cls, page, include_blocks=True):
        data = {
            'id': page.id,
            'title': page.title,
            'slug': page.slug,
            'status': page.status,
            'meta_description': page.meta_description or '',
            'show_in_header': page.show_in_header,
            'nav_label': page.nav_label or page.title,
            'nav_parent': page.nav_parent_id,
            'nav_parent_slug': page.nav_parent.slug if page.nav_parent else '',
            'nav_image_url': page.nav_image.url if page.nav_image else '',
            'header_group': page.header_group_id,
            'header_group_slug': page.header_group.slug if page.header_group else '',
            'sort_order': page.sort_order,
            'created_at': page.created_at,
            'updated_at': page.updated_at,
        }

        if include_blocks:
            data['blocks'] = [cls.serialize_block(block, page=page) for block in page.blocks.all()]


        return data

    @classmethod
    def serialize_block(cls, block, page=None):
        products = []
        product_ids = [int(pid) for pid in block.product_ids or [] if str(pid).isdigit()]

        # if block.block_type == 'products' and product_ids:
        #     product_qs = Products.objects.filter(id__in=product_ids).select_related(
        #         'category',
        #         'subcategory',
        #     ).prefetch_related('images', 'size_stocks')
        #     product_map = {product.id: cls.product_to_dict(product) for product in product_qs}
        #     products = [product_map[pid] for pid in product_ids if pid in product_map]
        # NAYA — replace karo upar wale se:
        if block.block_type == 'products':
            manual_qs = Products.objects.filter(id__in=product_ids).select_related(
                'category', 'subcategory','sub_subcategory',
            ).prefetch_related('images', 'size_stocks')
            product_map = {p.id: cls.product_to_dict(p) for p in manual_qs}
            products = [product_map[pid] for pid in product_ids if pid in product_map]

            if page is not None:
                page_title = (page.nav_label or page.title or '').strip()
                try:
                    from .models import SubCategory
                    matched_sub = SubCategory.objects.get(name__iexact=page_title)
                    auto_qs = Products.objects.filter(
                        subcategory=matched_sub,
                        category__name__iexact=page.header_group.title 
                    ).select_related('category', 'subcategory','sub_subcategory').prefetch_related('images', 'size_stocks')
                    existing_ids = {p['id'] for p in products}
                    for p in auto_qs:
                        if p.id not in existing_ids:
                            products.append(cls.product_to_dict(p))
                except SubCategory.DoesNotExist:
                    pass

        return {
            'id': block.id,
            'block_type': block.block_type,
            'title': block.title or '',
            'subtitle': block.subtitle or '',
            'height': block.height,
            'image_url': block.image.url if block.image else '',
            'video_url': block.video.url if block.video else '',
            'link': block.link or '',
            'product_ids': product_ids,
            'products': products,
            'settings': block.settings or {},
            'sort_order': block.sort_order,
        }

    @staticmethod
    def _load_blocks(request):
        try:
            blocks = json.loads(request.POST.get('blocks', '[]'))
        except json.JSONDecodeError as exc:
            raise ValueError('blocks must be valid JSON') from exc
        if not isinstance(blocks, list):
            raise ValueError('blocks must be a list')
        return blocks

    @staticmethod
    def _safe_int(value, default=0):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    @classmethod
    def save_page(cls, request, page=None):
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        if not title or not slug:
            raise ValueError('title and slug are required')

        page = page or CustomPage()
        page.title = title
        page.slug = slug
        page.status = request.POST.get('status', 'draft')
        page.meta_description = request.POST.get('meta_description', '')
        page.show_in_header = request.POST.get('show_in_header') == 'true'
        page.nav_label = request.POST.get('nav_label') or title
        page.sort_order = cls._safe_int(request.POST.get('sort_order'), 0)

        nav_parent = request.POST.get('nav_parent') or None
        page.nav_parent_id = nav_parent

        nav_image = request.FILES.get('nav_image')
        if nav_image:
            page.nav_image = nav_image

        header_group = request.POST.get('header_group') or None
        page.header_group_id = header_group

        page.save()

        existing_blocks = {block.id: block for block in page.blocks.all()}
        blocks = cls._load_blocks(request)
        page.blocks.all().delete()

        for index, block_data in enumerate(blocks):
            block_id = block_data.get('id')
            old_block = existing_blocks.get(block_id)
            block_uid = block_data.get('uid') or str(index)
            block_type = block_data.get('block_type', 'products')
            if block_type not in dict(PageBlock.BLOCK_CHOICES):
                block_type = 'products'

            product_ids = [
                int(pid)
                for pid in block_data.get('product_ids') or []
                if str(pid).isdigit()
            ]

            settings = block_data.get('settings') or {}
            if not isinstance(settings, dict):
                settings = {}

            block = PageBlock(
                page=page,
                block_type=block_type,
                title=block_data.get('title', ''),
                subtitle=block_data.get('subtitle', ''),
                height=cls._safe_int(block_data.get('height'), 520),
                link=block_data.get('link', ''),
                product_ids=product_ids,
                settings=settings,
                sort_order=index,
            )

            image_file = request.FILES.get(f'block_{block_uid}_image')
            video_file = request.FILES.get(f'block_{block_uid}_video')
            if image_file:
                block.image = image_file
            elif old_block and old_block.image:
                block.image = old_block.image

            if video_file:
                block.video = video_file
            elif old_block and old_block.video:
                block.video = old_block.video

            block.save()

        return page

    @staticmethod
    def serialize_header_group(group):
        return {
            'id': group.id,
            'title': group.title,
            'slug': group.slug,
            'direct_url': group.direct_url or '',
            'hover_title': group.hover_title or group.title,
            'hover_subtitle': group.hover_subtitle or '',
            'hover_image_url': group.hover_image.url if group.hover_image else '',
            'button_style': group.button_style,
            'sort_order': group.sort_order,
            'is_active': group.is_active,
            'show_dropdown': group.show_dropdown,
            'pages': [
                PageBuilderService.serialize_page(page, include_blocks=False)
                for page in group.pages.filter(status='published', show_in_header=True).order_by('sort_order', 'title')
            ],
        }

    @classmethod
    def save_header_group(cls, request, group=None):
        title = request.POST.get('title', '').strip()
        slug = request.POST.get('slug', '').strip()
        if not title or not slug:
            raise ValueError('title and slug are required')

        group = group or HeaderGroup()
        group.title = title
        group.slug = slug
        group.direct_url = request.POST.get('direct_url', '')
        group.hover_title = request.POST.get('hover_title', '') or title
        group.hover_subtitle = request.POST.get('hover_subtitle', '')
        group.button_style = request.POST.get('button_style', 'standard')
        group.sort_order = cls._safe_int(request.POST.get('sort_order'), 0)
        group.is_active = request.POST.get('is_active') == 'true'
        group.show_dropdown = request.POST.get('show_dropdown') == 'true'

        hover_image = request.FILES.get('hover_image')
        if hover_image:
            group.hover_image = hover_image

        group.save()
        return group

    @classmethod
    def seed_default_header_groups(cls):
        defaults = [
            {
                'title': "Ally's",
                'slug': 'allys',
                'direct_url': "/allproducts?category=ALLY'S",
                'hover_title': "Ally's",
                'hover_subtitle': 'Fancy and casual edits curated for color-rich wardrobes.',
                'button_style': 'standard',
                'sort_order': 10,
            },
            {
                'title': "Heera's",
                'slug': 'heeras',
                'direct_url': "/allproducts?category=HEERA'S",
                'hover_title': "Heera's",
                'hover_subtitle': 'A polished collection for everyday and occasion wear.',
                'button_style': 'standard',
                'sort_order': 20,
            },
            {
                'title': 'Rangraaz',
                'slug': 'rangraaz',
                'direct_url': '/allproducts?category=Rangraaz',
                'hover_title': 'Rangraaz',
                'hover_subtitle': 'Signature pieces, seasonal edits, and complete looks.',
                'button_style': 'featured',
                'sort_order': 30,
            },
            {
                'title': 'Sale',
                'slug': 'sale',
                'direct_url': '/allproducts?sale=true',
                'hover_title': 'Sale',
                'hover_subtitle': 'Limited-time price drops and seasonal offers.',
                'button_style': 'sale',
                'sort_order': 40,
                'show_dropdown': False,
            },
        ]

        for item in defaults:
            HeaderGroup.objects.get_or_create(slug=item['slug'], defaults=item)
