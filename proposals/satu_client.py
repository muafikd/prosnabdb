import requests
import logging
from .models import SystemSettings, Equipment

logger = logging.getLogger(__name__)

SATU_API_BASE = "https://my.satu.kz/api/v1"

def get_satu_token():
    settings = SystemSettings.get_settings()
    return settings.satu_api_token

import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape
from datetime import datetime
import io

def check_connection(token=None):
    """
    Check the connection to Satu API using the provided token (or from DB).
    """
    if not token:
        token = get_satu_token()
    if not token:
        return False, "Satu API Token is not set."
    
    url = f"{SATU_API_BASE}/products/list?limit=1"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return True, "Satu API connection successful"
        else:
            return False, f"Ошибка {response.status_code}: {response.text}"
    except Exception as e:
        logger.error(f"Satu API check connection failed: {e}")
        return False, str(e)

def _generate_satu_xml(equipments):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    xml_str = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE yml_catalog SYSTEM "shops.dtd">
<yml_catalog date="{now_str}">
    <shop>
        <name>Каталог Prosnab</name>
        <company>Prosnab</company>
        <currencies>
            <currency id="KZT" rate="1"/>
        </currencies>
        <categories>
            <category id="1">Оборудование</category>
        </categories>
        <offers>
'''
    for equip in equipments:
        price = float(equip.sale_price_kzt) if equip.sale_price_kzt else 1.0
        available = "true" if equip.is_published else "false"
        
        images = []
        if equip.equipment_imagelinks and isinstance(equip.equipment_imagelinks, list):
            images = [img for img in equip.equipment_imagelinks if isinstance(img, str) and img.startswith('http')]
            
        name = escape(equip.equipment_name or "")
        vendor_code = escape(equip.equipment_articule or "")
        manufacturer = equip.manufacturers.first()
        vendor = escape(manufacturer.manufacturer_name) if manufacturer else ""
        short_desc = equip.equipment_short_description or ""
        
        # Build detailed description
        desc_parts = []
        if short_desc:
            desc_parts.append(f"<p>{short_desc}</p>")
            
        specs = equip.specifications.all()
        if specs.exists():
            desc_parts.append("<h3>Технические характеристики:</h3><ul>")
            for spec in specs:
                desc_parts.append(f"<li><b>{escape(spec.spec_parameter_name)}:</b> {escape(spec.spec_parameter_value or '')}</li>")
            desc_parts.append("</ul>")
            
        full_description = "".join(desc_parts)
        
        xml_str += f'''            <offer id="{equip.equipment_id}" available="{available}">
                <name>{name}</name>
                <vendorCode>{vendor_code}</vendorCode>
                <vendor>{vendor}</vendor>
                <description><![CDATA[{full_description}]]></description>
                <price>{price}</price>
                <currencyId>KZT</currencyId>
                <categoryId>1</categoryId>
                <stock_quantity>100</stock_quantity>
'''
        for img in images:
            xml_str += f'''                <picture>{escape(img)}</picture>\n'''
            
        for spec in specs:
            spec_name = escape(spec.spec_parameter_name)
            spec_value = escape(spec.spec_parameter_value or "")
            xml_str += f'''                <param name="{spec_name}">{spec_value}</param>\n'''
            
        xml_str += f'''            </offer>\n'''

    xml_str += '''        </offers>
    </shop>
</yml_catalog>'''
    return xml_str

def export_equipment(equipment, is_bulk=False):
    """
    Export a single Equipment instance or a list of Equipment to Satu API via import_file.
    """
    token = get_satu_token()
    if not token:
        return False, "Satu API Token is not set."
        
    url = f"{SATU_API_BASE}/products/import_file"
    headers = {
        "Authorization": f"Bearer {token}"
    }

    if not isinstance(equipment, list):
        equipment_list = [equipment]
    else:
        equipment_list = equipment

    xml_content = _generate_satu_xml(equipment_list)
    files = {'file': ('export.xml', xml_content.encode('utf-8'), 'text/xml')}
    
    try:
        response = requests.post(url, headers=headers, files=files, timeout=30)
        logger.info(f"Satu API export response [{response.status_code}]: {response.text}")
        
        if response.status_code == 200:
            return True, response.json()
        else:
            error_text = response.text
            try:
                # Try to extract a clean error message from Satu's JSON response
                error_data = response.json()
                if 'error' in error_data and isinstance(error_data['error'], dict):
                    err_msg = error_data['error'].get('message', '')
                    if err_msg:
                        # Translate specific common API errors to user-friendly messages
                        if "ограничение на запуск одновременных импортов" in err_msg:
                            return False, "Импорт товаров на портал Satu уже запущен. Пожалуйста, дождитесь завершения предыдущего процесса импорта."
                        return False, f"Ошибка Satu API: {err_msg}"
            except Exception:
                pass # Fallback to raw text if it's not JSON
                
            return False, f"Ошибка {response.status_code}: {error_text}"
    except Exception as e:
        logger.error(f"Satu API export equipment failed: {e}")
        return False, f"Ошибка соединения с Satu API: {str(e)}"
