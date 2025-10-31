"""from datetime import datetime, timezone

Multi-Tenant Management & RBAC Routesfrom typing import List, Optional

"""

from fastapi import APIRouter, Depends, HTTPException, Header, Body

from fastapi import APIRouter, HTTPException, Queryfrom pydantic import BaseModel

from pydantic import BaseModel

from typing import List, Optionalfrom utils.gcp import get_firestore

from datetime import datetime, timezonefrom jose import jwt, JWTError

import uuidimport os



router = APIRouter()

router = APIRouter()



class TenantCreate(BaseModel):JWT_SECRET = os.getenv("JWT_SECRET", "change-this-in-prod")

    name: str

    plan: str = "starter"

    admin_email: strclass Tenant(BaseModel):

    name: str

    plan: str = "free"

class RoleAssignment(BaseModel):    active: bool = True

    user_id: str

    role: str

    permissions: List[str]def get_current_user(authorization: Optional[str] = Header(None)):

    if not authorization or not authorization.lower().startswith("bearer "):

        raise HTTPException(status_code=401, detail="Missing token")

@router.post("/tenants")    token = authorization.split(" ", 1)[1]

async def create_tenant(tenant: TenantCreate):    try:

    """Create new tenant"""        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])

            return payload

    tenant_id = f"tenant_{uuid.uuid4().hex[:10]}"    except JWTError:

            raise HTTPException(status_code=401, detail="Invalid token")

    return {

        "tenant_id": tenant_id,

        "name": tenant.name,@router.post("/tenants")

        "plan": tenant.plan,async def create_tenant(tenant: Tenant, user=Depends(get_current_user)):

        "status": "active",    # Require admin role

        "created_at": datetime.now(timezone.utc).isoformat()    roles = user.get("roles", [])

    }    if "admin" not in roles:

        raise HTTPException(status_code=403, detail="Admin role required")



@router.get("/tenants/{tenant_id}")    db = get_firestore()

async def get_tenant(tenant_id: str):    ref = db.collection("tenants").document()

    """Get tenant details"""    data = tenant.dict()

        data.update({

    return {        "created_at": datetime.now(timezone.utc).isoformat(),

        "tenant_id": tenant_id,        "owner_user": user.get("sub"),

        "name": "Demo Tenant",    })

        "plan": "enterprise",    ref.set(data)

        "status": "active",    return {"tenant_id": ref.id, **data}

        "users_count": 25,

        "api_usage": 125000,

        "created_at": datetime.now(timezone.utc).isoformat()@router.get("/tenants")

    }async def list_tenants(user=Depends(get_current_user)):

    # Admins see all, others see own

    db = get_firestore()

@router.get("/tenants")    if "admin" in user.get("roles", []):

async def list_tenants(limit: int = Query(50, ge=1, le=100)):        docs = db.collection("tenants").limit(50).stream()

    """List all tenants"""    else:

            docs = db.collection("tenants").where("owner_user", "==", user.get("sub")).stream()

    return {    items = [{"tenant_id": d.id, **d.to_dict()} for d in docs]

        "total": limit,    return {"tenants": items}

        "tenants": [

            {

                "tenant_id": f"tenant_{i}",class RoleAssignRequest(BaseModel):

                "name": f"Tenant {i}",    user_id: str

                "plan": "enterprise",    roles: List[str]

                "status": "active"

            }

            for i in range(1, min(limit + 1, 11))@router.post("/tenants/{tenant_id}/roles")

        ]async def assign_roles(tenant_id: str, body: RoleAssignRequest, user=Depends(get_current_user)):

    }    if "admin" not in user.get("roles", []):

        raise HTTPException(status_code=403, detail="Admin role required")

    db = get_firestore()

@router.post("/tenants/{tenant_id}/roles")    uref = db.collection("users").document(body.user_id)

async def assign_role(tenant_id: str, assignment: RoleAssignment):    snap = uref.get()

    """Assign role to user in tenant"""    if not snap.exists:

            raise HTTPException(status_code=404, detail="User not found")

    return {    data = snap.to_dict()

        "success": True,    data["roles"] = body.roles

        "tenant_id": tenant_id,    data["tenant_id"] = tenant_id

        "user_id": assignment.user_id,    uref.set(data)

        "role": assignment.role,    return {"user_id": body.user_id, "tenant_id": tenant_id, "roles": body.roles}

        "permissions": assignment.permissions
    }
