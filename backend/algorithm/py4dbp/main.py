from flask.typing import TeardownCallable
from werkzeug.wrappers import response
from .constants import RotationType, Axis
from .auxiliary_methods import intersect, set_to_decimal



DEFAULT_NUMBER_OF_DECIMALS = 3
START_POSITION = [0, 0, 0]


class Item:
    def __init__(self,ID ,name, width, height, depth, weight, type_index, Fitted_items=None):
        self.ID=ID
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.weight = weight
        self.area = height * width
        self.rotation_type = 0
        self.position = START_POSITION
        self.number_of_decimals = DEFAULT_NUMBER_OF_DECIMALS
        self.type_index=type_index
        self.Fitted_items=Fitted_items

    def format_numbers(self, number_of_decimals):
        self.width = set_to_decimal(self.width, number_of_decimals)
        self.height = set_to_decimal(self.height, number_of_decimals)
        self.depth = set_to_decimal(self.depth, number_of_decimals)
        self.weight = set_to_decimal(self.weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals

    def string(self):
        return f"""
        {self.name}:       
            ID:{self.ID}
            X:{self.width}, 
            Y:{self.height}, 
            Z:{self.depth}, 
            Weight:{self.weight}
            rotation:{self.rotation_type}
            position:{self.position}
        """
        #we have to covert the Decimal object to float so that
        #java packer will be happy
    def getResultDictionary(self):
        #conver position information into float

        if self.Fitted_items!=None:
            return{"ID":self.ID,
            "TypeName":self.name,
            "X":float(self.width),
            "Y":float(self.height),
            "Z":float(self.depth), 
            "Weight":float(self.weight),
            "position_x":float(self.position[0]),
            "position_y":float(self.position[1]),
            "position_z":float(self.position[2]),
            "RotationType":self.rotation_type,
            "TypeIndex":self.type_index,
            "Fitted_items":self.Fitted_items
            }
        else:
            return{"ID":self.ID,
            "TypeName":self.name,
            "X":float(self.width),
            "Y":float(self.height),
            "Z":float(self.depth), 
            "Weight":float(self.weight),
            "position_x":float(self.position[0]),
            "position_y":float(self.position[1]),
            "position_z":float(self.position[2]),
            "RotationType":self.rotation_type,
            "TypeIndex":self.type_index,
            }

    def get_volume(self):
        return set_to_decimal(
            self.width * self.height * self.depth, self.number_of_decimals
        )

    def get_dimension(self):
        if self.rotation_type == RotationType.RT_WHD:
            dimension = [self.width, self.height, self.depth]
        elif self.rotation_type == RotationType.RT_HWD:
            dimension = [self.height, self.width, self.depth]
        elif self.rotation_type == RotationType.RT_HDW:
            dimension = [self.height, self.depth, self.width]
        elif self.rotation_type == RotationType.RT_DHW:
            dimension = [self.depth, self.height, self.width]
        elif self.rotation_type == RotationType.RT_DWH:
            dimension = [self.depth, self.width, self.height]
        elif self.rotation_type == RotationType.RT_WDH:
            dimension = [self.width, self.depth, self.height]
        else:
            dimension = []

        return dimension


class Bin:
    def __init__(self, ID, name, width, height, depth, max_weight, type_index):
        self.ID=ID
        self.name = name
        self.width = width
        self.height = height
        self.depth = depth
        self.max_weight = max_weight
        self.items = []
        self.unfitted_items = []
        self.number_of_decimals = DEFAULT_NUMBER_OF_DECIMALS
        self.type_index=type_index

    def format_numbers(self, number_of_decimals):
        self.width = set_to_decimal(self.width, number_of_decimals)
        self.height = set_to_decimal(self.height, number_of_decimals)
        self.depth = set_to_decimal(self.depth, number_of_decimals)
        self.max_weight = set_to_decimal(self.max_weight, number_of_decimals)
        self.number_of_decimals = number_of_decimals

    def get_unfitted_items_as_dict_array(self):
        unFittedItemArray=[]
        for unfitted_item in self.unfitted_items:
            unFittedItemArray.append(unfitted_item.getResultDictionary())
        return unFittedItemArray
        
    def string(self):
        return f"""
            ID:{self.ID},
            TypeName:{self.name},
            X:{float(self.width)}, 
            Y:{float(self.height)}, 
            Z:{float(self.depth)}, 
            Weight_limmit:{float(self.max_weight)}
        """
    def getResultDictionary(self):
        #convet Fitted_items to dictionary(array of dics)
        FittedItemArray=[]
        for fitted_item in self.items:
            FittedItemArray.append(fitted_item.getResultDictionary())
        

        unFittedItemArray=[]
        #convert unfitted_items to array of dictionary
        for unfitted_item in self.unfitted_items:
            unFittedItemArray.append(unfitted_item.getResultDictionary())


        return{
            "ID":self.ID,
            "TypeName":self.name,
            "TypeIndex":self.type_index,
            "X":float(self.width),
            "Y":float(self.height),
            "Z":float(self.depth),
            "Weight_limmit":float(self.max_weight),
            "Fitted_items":FittedItemArray,
            "UnFitted_items":unFittedItemArray,
    }

    def get_volume(self):
        return set_to_decimal(
            self.width * self.height * self.depth, self.number_of_decimals
        )

    def get_total_weight(self):
        total_weight = 0

        for item in self.items:
            total_weight += item.weight

        return set_to_decimal(total_weight, self.number_of_decimals)

    def put_item(self, item, pivot):
        fit = False
        valid_item_position = item.position
        item.position = pivot

        for i in range(0, len(RotationType.ALL)):
            item.rotation_type = i
            dimension = item.get_dimension()
            if (
                self.width < pivot[0] + dimension[0] or
                self.height < pivot[1] + dimension[1] or
                self.depth < pivot[2] + dimension[2]
            ):
                continue

            fit = True

            for current_item_in_bin in self.items:
                if intersect(current_item_in_bin, item):
                    fit = False
                    break

            if fit:
                if self.get_total_weight() + item.weight > self.max_weight:
                    fit = False
                    return fit

                self.items.append(item)

            if not fit:
                item.position = valid_item_position

            return fit

        if not fit:
            item.position = valid_item_position

        return fit

    def put_item_only_2D_rotate(self, item, pivot):
        fit = False
        valid_item_position = item.position
        item.position = pivot

        for i in range(0, len(RotationType.TWO_D)):
            item.rotation_type = RotationType.TWO_D[i]
            dimension = item.get_dimension()
            if (
                self.width < pivot[0] + dimension[0] or
                self.height < pivot[1] + dimension[1] or
                self.depth < pivot[2] + dimension[2]
            ):
                continue

            fit = True

            for current_item_in_bin in self.items:
                if intersect(current_item_in_bin, item):
                    fit = False
                    break

            if fit:
                if self.get_total_weight() + item.weight > self.max_weight:
                    fit = False
                    return fit

                self.items.append(item)

            if not fit:
                item.position = valid_item_position

            return fit

        if not fit:
            item.position = valid_item_position

        return fit



class Packer:
    def __init__(self, TWO_D_MODE=False):
        self.bins = []
        self.items = []
        self.unfit_items = []
        self.total_items = 0
        self.TWO_D_MODE=TWO_D_MODE
        print("Packer init")

    def add_bin(self, bin):
        print("add bin")
        return self.bins.append(bin)

    def add_item(self, item):
        self.total_items = len(self.items) + 1

        return self.items.append(item)

    def pack_to_bin(self, bin, item):
        fitted = False
        if not bin.items:
            if self.TWO_D_MODE:
                response=bin.put_item_only_2D_rotate(item, START_POSITION)
            response = bin.put_item(item, START_POSITION)

            if not response:
                bin.unfitted_items.append(item)

            return

        for axis in range(0, 3):
            items_in_bin = bin.items

            for ib in items_in_bin:
                pivot = [0, 0, 0]
                w, h, d = ib.get_dimension()
                if axis == Axis.WIDTH:
                    pivot = [
                        ib.position[0] + w,
                        ib.position[1],
                        ib.position[2]
                    ]
                elif axis == Axis.HEIGHT:
                    pivot = [
                        ib.position[0],
                        ib.position[1] + h,
                        ib.position[2]
                    ]
                elif axis == Axis.DEPTH:
                    pivot = [
                        ib.position[0],
                        ib.position[1],
                        ib.position[2] + d
                    ]


                if self.TWO_D_MODE:
                    if bin.put_item_only_2D_rotate(item, pivot):
                        fitted = True
                        break
                else:
                    if bin.put_item(item, pivot):
                        fitted = True
                        break
            if fitted:
                break

        if not fitted:
            bin.unfitted_items.append(item)
    def pack_to_bin_self_def(self, pos, limit_h, limit_w, Items, num_items, bin):
        if(num_items == 0):
            return

        vsp = [pos]
        #put in Bin
        next_board = []
        remain_items = []
        for i in range(len(Items)):
            pos_erase = -1
            p = [-1,-1,-1]
            p1 = [-1,-1,-1]
            p2 = [-1,-1,-1]
            for pos_i in range(len(vsp)):
                # find valid position
                if Items[i].height <= limit_h and Items[i].width <= limit_w and vsp[pos_i][0] + Items[i].height <= bin.height and vsp[pos_i][1] + Items[i].width <= bin.width and vsp[pos_i][2] + Items[i].depth <= bin.depth:
                    pos_erase = pos_i
                    p = vsp[pos_i]
                    Items[i].position = p
                    print(str(Items[i].ID) + ": " + str(Items[i].position))
                    next_board.append([[p[0], p[1], p[2] + Items[i].depth], Items[i].height, Items[i].width])
                    p1 = [p[0] + Items[i].height, p[1], p[2]]
                    p2 = [p[0], p[1] + Items[i].width, p[2]]
                    break

            if pos_erase != -1:    
                vsp.pop(pos_erase)
                vsp.append(p1)
                vsp.append(p2)
            else:
                remain_items.append(Items[i])

        if len(remain_items) == num_items:
            return

        num_items = len(remain_items)
        for b in next_board:
            self.pack_to_bin_self_def(b[0], b[1], b[2], remain_items, num_items)

    def pack(
        self, bigger_first=False, distribute_items=False,
        number_of_decimals=DEFAULT_NUMBER_OF_DECIMALS
    ):
        print("into pack()")
        for bin in self.bins:
            bin.format_numbers(number_of_decimals)

        for item in self.items:
            item.format_numbers(number_of_decimals)

        self.bins.sort(
            key=lambda bin: bin.get_volume(), reverse=bigger_first
        )
        self.items.sort(
            key=lambda item: item.get_volume(), reverse=bigger_first
        )

        for it in self.items:
            l = [it.width, it.height, it.depth].sort()
            it.depth, it.width, it.height = l[0], l[1], l[2]

        self.items.sort(key = lambda s: s.area, reverse = True)
        print(f'{self.bins=}')
        for bin in self.bins:
            # bin.height, bin.width = bin.width, bin.height
            print(f'{bin.height=}')
            print(f'{bin.width=}')
            print(f'{bin.depth=}')

            self.pack_to_bin_self_def(START_POSITION, bin.height, bin.width, self.items, len(self.items), bin)

            if distribute_items:
                for item in bin.items:
                    self.items.remove(item)

