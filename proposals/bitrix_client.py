"""
Bitrix24 REST API client via webhook.
Webhook URL format: https://your-domain.bitrix24.com/rest/1/CODE/
Method is appended: .../crm.company.list
"""
import logging
import requests

logger = logging.getLogger(__name__)


def _method_url(webhook_url, method):
    base = (webhook_url or '').rstrip('/')
    if not base:
        return None
    return f"{base}/{method}"


def bitrix_call(webhook_url, method, params=None):
    """
    Call Bitrix24 REST API method.
    :param webhook_url: Base webhook URL (e.g. https://xxx.bitrix24.com/rest/1/CODE/)
    :param method: Method name (e.g. crm.company.list)
    :param params: Dict of query parameters
    :return: (success: bool, result or error_message)
    """
    if not webhook_url or not webhook_url.strip():
        return False, "URL вебхука не задан"
    url = _method_url(webhook_url.strip(), method)
    if not url:
        return False, "Неверный URL вебхука"
    try:
        r = requests.get(url, params=params or {}, timeout=15)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            return False, data.get("error_description", data.get("error", "Ошибка Bitrix24"))
        return True, data.get("result", data)
    except requests.RequestException as e:
        logger.exception("Bitrix24 request failed")
        return False, str(e) or "Ошибка соединения с Bitrix24"
    except ValueError as e:
        return False, "Неверный ответ от Bitrix24"


def _flat_params(order_dict, select_list, start=0, filter_dict=None):
    """Build flat query params for Bitrix list methods."""
    params = {"start": start}
    if order_dict:
        for k, v in order_dict.items():
            params[f"order[{k}]"] = v
    if select_list:
        params["select[]"] = select_list
    if filter_dict:
        for k, v in filter_dict.items():
            params[f"filter[{k}]"] = v
    return params


def check_connection(webhook_url):
    """Check connection: crm.company.list with limit 1."""
    params = _flat_params({"ID": "ASC"}, ["ID", "TITLE"], 0)
    ok, result = bitrix_call(webhook_url, "crm.company.list", params)
    if not ok:
        return False, result
    # result can be list or dict with 'result' key depending on API version
    if isinstance(result, dict) and "result" in result:
        result = result["result"]
    return True, result


def search_companies_by_title(webhook_url, query, limit=20):
    """Search companies by title (TITLE). Substring: filter[%TITLE]=query."""
    select = ["ID", "TITLE", "PHONE", "EMAIL", "ADDRESS", "ADDRESS_LEGAL", "UF_CRM_LEGALENTITY_INN", "UF_CRM_1657870237252"]
    params = _flat_params({"ID": "DESC"}, select, 0, {"%TITLE": query})
    ok, result = bitrix_call(webhook_url, "crm.company.list", params)
    if not ok:
        return ok, result
    items = result if isinstance(result, list) else (result.get("result") or result)
    if isinstance(items, dict):
        items = items.get("result", [])
    if not isinstance(items, list):
        items = []
    return True, items[:limit]


def search_contacts_for_companies(webhook_url, query, limit=20):
    """
    Search contacts by name or phone, then resolve to companies.
    Returns list of companies (with ID, TITLE, etc.) from COMPANY_ID of matching contacts.
    """
    # Search contacts: try NAME and PHONE substring
    params = _flat_params({}, ["ID", "NAME", "PHONE", "EMAIL", "COMPANY_ID", "COMPANY_TITLE"], 0, {"%NAME": query})
    ok, result = bitrix_call(webhook_url, "crm.contact.list", params)
    if not ok:
        return ok, result
    contacts = result if isinstance(result, list) else (result.get("result") or result)
    if isinstance(contacts, dict):
        contacts = contacts.get("result", [])
    if not isinstance(contacts, list):
        contacts = []
    company_ids = []
    seen = set()
    for c in contacts:
        cid = c.get("COMPANY_ID") or c.get("companyId")
        if cid and cid not in seen:
            seen.add(cid)
            company_ids.append(cid)
    if not company_ids:
        return True, []
    # Fetch companies by IDs (Bitrix filter[ID]=1|2|3)
    id_list = company_ids[:limit]
    filter_ids = "|".join(str(i) for i in id_list)
    select = ["ID", "TITLE", "PHONE", "EMAIL", "ADDRESS", "ADDRESS_LEGAL", "UF_CRM_LEGALENTITY_INN", "UF_CRM_1657870237252"]
    params2 = _flat_params({"ID": "DESC"}, select, 0, {"ID": filter_ids})
    ok2, result2 = bitrix_call(webhook_url, "crm.company.list", params2)
    if not ok2:
        return ok2, result2
    companies = result2 if isinstance(result2, list) else (result2.get("result") or result2)
    if isinstance(companies, dict):
        companies = companies.get("result", [])
    if not isinstance(companies, list):
        companies = []
    return True, companies[:limit]


def search_companies_by_requisite(webhook_url, query, limit=20):
    """
    Search by IIN/BIN. Try company list with common BIN/INN field filters;
    if no results, try crm.requisite.list (entity type 4 = company) and resolve company IDs.
    """
    select = ["ID", "TITLE", "PHONE", "EMAIL", "ADDRESS", "ADDRESS_LEGAL", "UF_CRM_LEGALENTITY_INN", "UF_CRM_1657870237252"]
    for field in ("UF_CRM_LEGALENTITY_INN", "UF_CRM_1657870237252", "UF_CRM_COMPANY_INN"):
        params = _flat_params({"ID": "DESC"}, select, 0, {"%" + field: query})
        ok, result = bitrix_call(webhook_url, "crm.company.list", params)
        if not ok:
            return ok, result
        items = result if isinstance(result, list) else (result.get("result") or result)
        if isinstance(items, dict):
            items = items.get("result", [])
        if isinstance(items, list) and len(items) > 0:
            return True, items[:limit]
    # Fallback: requisite.list (entityTypeId 4 = company), filter by RQ_INN if supported
    params = _flat_params({}, ["ID", "ENTITY_ID", "RQ_INN", "RQ_KPP"], 0, {"ENTITY_TYPE_ID": 4, "%RQ_INN": query})
    ok, result = bitrix_call(webhook_url, "crm.requisite.list", params)
    if not ok:
        return True, []  # No requisite search, return empty
    req_list = result if isinstance(result, list) else (result.get("result") or result)
    if isinstance(req_list, dict):
        req_list = req_list.get("result", [])
    if not isinstance(req_list, list):
        return True, []
    entity_ids = []
    seen = set()
    for r in req_list:
        eid = r.get("ENTITY_ID") or r.get("entityId")
        if eid and eid not in seen:
            seen.add(eid)
            entity_ids.append(eid)
    if not entity_ids:
        return True, []
    filter_ids = "|".join(str(i) for i in entity_ids[:limit])
    params2 = _flat_params({"ID": "DESC"}, select, 0, {"ID": filter_ids})
    ok2, result2 = bitrix_call(webhook_url, "crm.company.list", params2)
    if not ok2:
        return ok2, result2
    companies = result2 if isinstance(result2, list) else (result2.get("result") or result2)
    if isinstance(companies, dict):
        companies = companies.get("result", [])
    if not isinstance(companies, list):
        companies = []
    return True, companies[:limit]


def get_company_by_id(webhook_url, company_id):
    """Get single company by ID."""
    ok, result = bitrix_call(
        webhook_url,
        "crm.company.get",
        {"id": company_id}
    )
    if not ok:
        return ok, result
    return True, result if isinstance(result, dict) else {}


def get_company_requisites(webhook_url, company_id):
    """Get requisites for company (entityTypeId 4, entityId = company_id)."""
    params = _flat_params(
        {}, ["ID", "RQ_INN", "RQ_KPP", "RQ_ADDR", "RQ_BANK_NAME", "RQ_ACC_NUM", "RQ_BIK", "RQ_BANK_ADDR"], 0,
        {"ENTITY_TYPE_ID": 4, "ENTITY_ID": company_id}
    )
    ok, result = bitrix_call(webhook_url, "crm.requisite.list", params)
    if not ok:
        return ok, result
    items = result if isinstance(result, list) else (result.get("result") or result)
    if isinstance(items, dict):
        items = items.get("result", [])
    return True, items if isinstance(items, list) else []
