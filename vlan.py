from dataclasses import dataclass

@dataclass
class Vlan:
    id: int
    nom: str
    status: str = "down"
    vlan: int | None = None

Vlans = [Vlan(13,"vlan 1","premier composant"),
        Vlan(7,"vlan 1","second composant"),
        Vlan(7,"vlan 1","troisieme composant")]

for vlan in Vlans:
    if vlan.id > 10:
        print(vlan)