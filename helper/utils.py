import discord

async def roledown(botrole,userrole):
  if botrole.position > userrole.position:
    return False
  else:
    return True

async def checkdng(role):
  if role.permissions.administrator or role.permissions.manage_guild or role.permissions.manage_channels or role.permissions.manage_roles or role.permissions.manage_emojis_and_stickers:
    return False
  else:
    return True

def checkrol(role):
  perms = ""
  for p in role.permissions:
    xd = p[0]
    wp = xd.replace("_", " ")
    perms+=f"{xd.replace('_', ' ')}, "
  if perms == "":
    perms+="None"
  else:
    perms.replace("_", " ")
    perms.strip(", ")
  return perms
